# auth_app/views.py
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from .models import PerfilUsuario, user_es_profesor
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

# DRF y JWT
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer

# reCAPTCHA
import requests
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# ------------------------------
# FUNCIONES AUXILIARES
# ------------------------------

def validar_recaptcha(token):
    """Valida el token de reCAPTCHA.
    En DEBUG (local) o sin clave configurada, se omite para permitir registro offline.
    En producción se valida contra Google.
    """
    from django.conf import settings
    secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    if not secret or getattr(settings, 'DEBUG', False):
        return True  # modo local/desarrollo: no bloquear el registro
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": secret,
        "response": token
    }
    try:
        resp = requests.post(url, data=data, timeout=5)
        result = resp.json()
        return result.get("success", False)
    except requests.RequestException:
        return False

def validar_password_segura(password):
    """
    Valida que la contraseña cumpla con requisitos de seguridad
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe tener al menos una letra mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe tener al menos una letra minúscula"
    
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe tener al menos un número"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe tener al menos un carácter especial (!@#$%^&* etc.)"
    
    return True, "Contraseña válida"

def validar_email_unico_y_valido(email):
    """
    Valida que el email sea único y tenga formato válido
    """
    try:
        validate_email(email)
    except ValidationError:
        return False, "El formato del email no es válido"
    
    if User.objects.filter(email=email).exists():
        return False, "El correo electrónico ya está registrado"
    
    return True, "Email válido"

# ------------------------------
# VISTAS NORMALES (Django Template)
# ------------------------------

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if user.is_superuser:
                return redirect("/admin/")
            elif user_es_profesor(user):
                return redirect("dashboard:dashboard_profesor")
            else:
                return redirect("dashboard:dashboard_user")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, "login.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        rol = request.POST.get("rol")
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        institucion = request.POST.get("institucion", "").strip()

        # Validaciones básicas
        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect("register")

        if rol not in ["estudiante", "profesor"]:
            messages.error(request, "Rol no válido")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe")
            return redirect("register")

        es_profesor = rol == "profesor"

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=nombre,
            last_name=apellido,
            is_superuser=False,
            is_staff=es_profesor
        )

        # Crear perfil y mantener sincronizado el rol
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={
                'institucion': institucion if institucion else None,
                'foto_perfil': 'img/default_user.png',
                'is_teacher': es_profesor,
            },
        )

        # Iniciar sesión automáticamente
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Redirección según rol
        if es_profesor:
            messages.success(request, f"✅ Bienvenido profesor {nombre} {apellido}")
            return redirect("dashboard:dashboard_profesor")
        else:
            messages.success(request, f"✅ Bienvenido {nombre} {apellido}")
            return redirect("dashboard:dashboard_user")
    return render(request, "register.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def privacy_policy_view(request):
    return render(request, "privacy.html")

# ------------------------------
# VISTAS API (DRF + JWT)
# ------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Login vía API, devuelve access y refresh JWT."""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })
    return Response({'error': 'Usuario o contraseña incorrectos'}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Registro vía API seguro con JWT usando serializer."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Asignar rol si viene en la data
        rol = request.data.get("rol", "").lower()
        if rol == "profesor":
            user.is_staff = True
            user.save()
        else:
            user.is_staff = False

        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Usuario registrado exitosamente.',
            'username': user.username,
            'email': user.email,
            'rol': rol if rol in ["profesor", "estudiante"] else "estudiante",
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register_session(request):
    """Registro vía API con sesión Django y reCAPTCHA"""
    data = request.data
    
    # ✅ Validar reCAPTCHA solo si está configurado y no es DEBUG
    from django.conf import settings as _s
    recaptcha_token = data.get("g-recaptcha-response")
    if _s.RECAPTCHA_SECRET_KEY and not _s.DEBUG:
        if not recaptcha_token or not validar_recaptcha(recaptcha_token):
            return Response({'error': 'Captcha inválido. Por favor intenta de nuevo.'}, status=400)
    
    # Validaciones básicas
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password1 = data.get("password1", "").strip()
    password2 = data.get("password2", "").strip()
    rol = data.get("rol", "").strip()
    nombre_completo = data.get("nombre_completo", "").strip()
    alias = (data.get("alias") or "").strip() or None
    institucion = data.get("institucion", "").strip()
    semestre = data.get("semestre", "").strip() if rol == "estudiante" else None

    if not username or not email or not password1 or not password2 or not nombre_completo:
        return Response({'error': 'Por favor completa todos los campos obligatorios.'}, status=400)

    if password1 != password2:
        return Response({'error': 'Las contraseñas no coinciden.'}, status=400)

    if rol not in ["estudiante", "profesor"]:
        return Response({'error': 'Rol no válido.'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'El usuario ya existe.'}, status=400)

    # ✅ Validación de email mejorada
    email_valido, mensaje_email = validar_email_unico_y_valido(email)
    if not email_valido:
        return Response({'error': mensaje_email}, status=400)

    # ✅ Validación de contraseña segura
    es_segura, mensaje_error = validar_password_segura(password1)
    if not es_segura:
        return Response({'error': mensaje_error}, status=400)

    # Dividir nombre completo
    partes = nombre_completo.split(" ", 1)
    first_name = partes[0] if partes else ""
    last_name = partes[1] if len(partes) > 1 else ""

    try:
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=(rol == "profesor"),
            is_superuser=False
        )

        # Crear perfil (SOLO UNA VEZ)
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={
                'institucion': institucion if institucion else None,
                'alias': alias,
                'semestre': semestre if semestre else None,
                'is_teacher': (rol == "profesor"),
                'foto_perfil': 'img/default_user.png',
            },
        )

        # ✅ SOLUCIÓN: Especificar el backend manualmente antes del login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        
        # Autenticación y tokens
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Usuario registrado exitosamente.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'rol': rol,
            'usuario': username
        }, status=201)

    except Exception as e:
        return Response({'error': f'Error al crear el usuario: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login_session(request):
    """Login vía API con sesión Django - VERSIÓN SIMPLE Y FUNCIONAL"""
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()

    # Validaciones básicas
    if not username or not password:
        return Response({
            'error': 'Por favor ingresa usuario y contraseña'
        }, status=400)

    # Autenticar
    user = authenticate(
        request, 
        username=username, 
        password=password,
        backend='django.contrib.auth.backends.ModelBackend'
    )

    if user:
        # ✅ Login exitoso
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        refresh = RefreshToken.for_user(user)

        # Determinar rol
        if user.is_superuser:
            rol = "admin"
        elif user.is_staff:
            rol = "profesor"
        else:
            rol = "estudiante"

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'rol': rol,
            'username': user.username,
            'nombre_completo': f"{user.first_name} {user.last_name}",
            'message': 'Login exitoso'
        })

    else:
        # ✅ Login fallido
        return Response({
            'error': 'Usuario o contraseña incorrectos'
        }, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def verificar_intentos(request, username):
    """Endpoint para verificar intentos de un usuario"""
    from .utils import obtener_estado_intentos
    
    info = obtener_estado_intentos(username)
    return Response(info)

# ------------------------------
# VISTAS DE DASHBOARD
# ------------------------------

@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    elif user.is_staff:
        return redirect('dashboard:dashboard_profesor')
    else:
        return redirect('dashboard:dashboard_user')

@login_required
def estudiante_dashboard(request):
    context = {
        "recursos": [
            {"nombre": "Curso A", "completado": True},
            {"nombre": "Curso B", "completado": False},
        ]
    }
    return render(request, "dashboard_user.html", context)

@login_required
def profesor_dashboard(request):
    cursos = [
        {"nombre": "Matemáticas I", "grupo": "1A", "alumnos": 30},
        {"nombre": "Historia", "grupo": "2B", "alumnos": 25},
    ]
    context = {
        "cursos": cursos,
        "cursos_activos": len(cursos),
        "alumnos_inscritos": sum(c['alumnos'] for c in cursos),
        "tareas_revisadas": 10,
        "material_subido": 5,
    }
    return render(request, "dashboard_profesor.html", context)

# ------------------------------
# VISTAS DE CONFIGURACIÓN
# ------------------------------

@login_required
def configuracion_view(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    return render(request, "configuracion.html", {"perfil": perfil})

class EditarPerfilForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150, required=False, disabled=True)
    first_name = forms.CharField(label="Nombre", max_length=150, required=False)
    last_name = forms.CharField(label="Apellido", max_length=150, required=False)

    class Meta:
        model = PerfilUsuario
        fields = ['foto_perfil']  # Solo este campo viene del modelo PerfilUsuario

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = user.username
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name

    def save(self, commit=True):
        perfil = super().save(commit=False)
        user = perfil.user
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        if commit:
            user.save()
            perfil.save()
        return perfil

@login_required
def editar_perfil_view(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Perfil actualizado correctamente.")

            # Redirección según el tipo de usuario
            if request.user.is_superuser:
                return redirect('/admin/')
            elif request.user.is_staff:
                return redirect('configuracion_profesor')
            else:
                return redirect('configuracion')
    else:
        form = EditarPerfilForm(instance=perfil, user=request.user)

    return render(request, "editar_perfil.html", {"form": form})

@login_required
def eliminar_cuenta(request):
    """Elimina la cuenta del usuario logueado"""
    user = request.user
    logout(request)
    user.delete()
    return render(request, "eliminacion_exitosa.html", {"username": user.username})

@login_required
def configuracion_profesor_view(request):
    messages.get_messages(request).used = True
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)

    if not request.user.is_staff:
        messages.warning(request, "Acceso restringido a profesores.")
        return redirect("dashboard:dashboard_user")

    context = {"perfil": perfil}
    return render(request, "configuracion_profesor.html", context)

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'

    def get_success_url(self):
        user = self.request.user
        # Redirección según el tipo de usuario
        if user.is_superuser:
            return reverse_lazy('admin_dashboard')
        elif user.is_staff:
            return reverse_lazy('configuracion_profesor')
        else:
            return reverse_lazy('configuracion')

# ------------------------------
# VISTAS DE ADMINISTRADOR
# ------------------------------

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Acceso restringido al administrador.")
        return redirect("dashboard:dashboard_user")
    return redirect("/admin/")

@login_required
def admin_cursos(request):
    if not request.user.is_superuser:
        messages.error(request, "Acceso restringido al administrador.")
        return redirect("dashboard:dashboard_user")

    try:
        from resources.models import Material
        cursos = Material.objects.all()
    except ImportError:
        cursos = []

    context = {"cursos": cursos}
    return render(request, "admin_cursos.html", context)

@login_required
def admin_usuarios(request):
    if not request.user.is_superuser:
        messages.error(request, "Acceso restringido al administrador.")
        return redirect("dashboard:dashboard_user")

    usuarios = []
    for user in User.objects.all():
        if user.is_superuser:
            rol = "Administrador"
        elif user.is_staff:
            rol = "Profesor"
        else:
            rol = "Estudiante"
        perfil = getattr(user, "perfilusuario", None)
        institucion = perfil.institucion if perfil else "—"
        usuarios.append({
            "id": user.id,
            "username": user.username,
            "nombre": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "rol": rol,
            "institucion": institucion,
            "activo": user.is_active
        })

    context = {"usuarios": usuarios, "total_usuarios": len(usuarios)}
    return render(request, "admin_usuarios.html", context)

@login_required
def admin_estadisticas(request):
    if not request.user.is_superuser:
        messages.error(request, "Acceso restringido al administrador.")
        return redirect("dashboard:dashboard_user")

    total_usuarios = User.objects.count()
    total_profesores = User.objects.filter(is_staff=True).count()
    total_estudiantes = User.objects.filter(is_staff=False, is_superuser=False).count()

    context = {
        "total_usuarios": total_usuarios,
        "total_profesores": total_profesores,
        "total_estudiantes": total_estudiantes
    }
    return render(request, "admin_estadisticas.html", context)