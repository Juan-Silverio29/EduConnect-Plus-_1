from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import os
import json
import pandas as pd
import plotly.express as px
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from dashboard.models import Actividad
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse  # <-- IMPORT IMPORTANTE
from .models import Curso, Actividad, Tarea, EntregaTarea, MaterialDidactico, Inscripcion


# Modelos
from .models import (
    Curso, Inscripcion, MaterialDidactico,
    Evaluacion, UserActivity, LearningSession,
    Tarea, EntregaTarea
)

from auth_app.models import PerfilUsuario
from forum.models import Foro
from dashboard.models import UserActivity, LearningSession
from .models import Curso, Inscripcion, MaterialDidactico, Evaluacion

# ===========================
# 🏆 SISTEMA DE INSIGNIAS
# ===========================
CATALOGO_INSIGNIAS = [
    {'codigo': 'primer_curso',   'nombre': '🎓 Primer Paso',        'descripcion': 'Te inscribiste a tu primer curso'},
    {'codigo': 'tres_cursos',    'nombre': '📚 Estudiante Activo',  'descripcion': 'Inscrito en 3 o más cursos'},
    {'codigo': 'primera_tarea',  'nombre': '✍️ A Prender',           'descripcion': 'Entregaste tu primera tarea'},
    {'codigo': 'cinco_tareas',   'nombre': '📝 Trabajador',         'descripcion': 'Has entregado 5 tareas'},
    {'codigo': 'primer_recurso', 'nombre': '📤 Colaborador',        'descripcion': 'Subiste tu primer recurso a la plataforma'},
    {'codigo': 'primer_foro',    'nombre': '💬 Participativo',      'descripcion': 'Creaste tu primera publicación en el foro'},
    {'codigo': 'curioso_ia',     'nombre': '🤖 Curioso',            'descripcion': 'Usaste el asistente IA para aprender'},
]

def otorgar_insignia(usuario, codigo):
    """Otorga una insignia al usuario si no la tiene ya. Devuelve la insignia o None."""
    from django.core.cache import cache
    key = f'insignia_{usuario.id}_{codigo}'
    if cache.get(key):
        return None
    cache.set(key, True, 60 * 60 * 24 * 365)  # marcado por 1 año
    return {'codigo': codigo, **next((i for i in CATALOGO_INSIGNIAS if i['codigo'] == codigo), {})}

def insignias_de(usuario):
    """Lista de insignias obtenidas por el usuario (derivadas de sus acciones reales)."""
    from django.core.cache import cache
    obtenidas = []
    for ins in CATALOGO_INSIGNIAS:
        if cache.get(f'insignia_{usuario.id}_{ins["codigo"]}'):
            obtenidas.append(ins)
    return obtenidas

def evaluar_insignias(usuario):
    """Evalúa todas las reglas de insignias según actividad real.
    Solo aplica a ESTUDIANTES: los profesores no ganan insignias de aprendizaje.
    """
    # Los profesores/admin no participan del sistema de insignias
    if usuario.is_staff or usuario.is_superuser:
        return []
    try:
        if usuario.perfilusuario.is_teacher:
            return []
    except Exception:
        pass

    nuevas = []
    n_cursos = Inscripcion.objects.filter(alumno=usuario).count()
    n_tareas = EntregaTarea.objects.filter(alumno=usuario).count()
    n_foros = Foro.objects.filter(usuario=usuario).count() if hasattr(Foro, 'usuario') else 0
    
    if n_cursos >= 1 and otorgar_insignia(usuario, 'primer_curso'):
        nuevas.append('primer_curso')
    if n_cursos >= 3 and otorgar_insignia(usuario, 'tres_cursos'):
        nuevas.append('tres_cursos')
    if n_tareas >= 1 and otorgar_insignia(usuario, 'primera_tarea'):
        nuevas.append('primera_tarea')
    if n_tareas >= 5 and otorgar_insignia(usuario, 'cinco_tareas'):
        nuevas.append('cinco_tareas')
    if n_foros >= 1 and otorgar_insignia(usuario, 'primer_foro'):
        nuevas.append('primer_foro')
    return nuevas

# Formularios
from .forms import CursoForm, MaterialForm, EvaluacionForm

# ---------------------------
# Redirección según el rol
# ---------------------------

@login_required
def dashboard_view(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('dashboard:dashboard_admin')
    elif hasattr(user, "perfilusuario") and getattr(user.perfilusuario, "is_teacher", False):
        return redirect('dashboard:dashboard_profesor')
    else:
        return redirect('dashboard:dashboard_user')

# ---------------------------
# DASHBOARD: ADMINISTRADOR
# ---------------------------

@login_required
def dashboard_admin(request):
    if not request.user.is_staff:
        messages.error(request, "❌ No tienes permisos para acceder al panel de administración.")
        return redirect('dashboard:dashboard_user')
    
    total_usuarios = User.objects.count()
    total_profesores = PerfilUsuario.objects.filter(is_teacher=True).count()
    total_cursos = Curso.objects.count()  # Ahora dinámico
    
    context = {
        "total_usuarios": total_usuarios,
        "total_profesores": total_profesores,
        "total_cursos": total_cursos,
    }
    return render(request, "dashboard_admin.html", context)

@login_required
def admin_usuarios(request):
    usuarios = PerfilUsuario.objects.select_related('user').all()
    return render(request, "admin_usuarios.html", {"usuarios": usuarios})

@login_required
def admin_cursos(request):
    cursos = Curso.objects.select_related('profesor').all()
    return render(request, "admin_cursos.html", {"cursos": cursos})

@login_required
def admin_estadisticas(request):
    data = {
        "usuarios": User.objects.count(),
        "profesores": PerfilUsuario.objects.filter(is_teacher=True).count(),
        "cursos": Curso.objects.count(),
    }
    return render(request, "admin_estadisticas.html", data)

# ---------------------------
# DASHBOARD: PROFESOR
# ---------------------------

@login_required
def dashboard_profesor(request):
    profesor = request.user
    
    # Cursos activos creados por el profesor
    cursos_activos = Curso.objects.filter(profesor=profesor).count()
    
    # Cursos recientes para mostrar
    cursos = Curso.objects.filter(profesor=profesor).order_by('-fecha_creacion')[:4]
    
    # Alumnos inscritos en los cursos del profesor
    alumnos_inscritos = Inscripcion.objects.filter(curso__profesor=profesor).count()
    
    # Materiales subidos por el profesor
    materiales_subidos = MaterialDidactico.objects.filter(profesor=profesor).count()
    
    # Evaluaciones próximas
    evaluaciones = Evaluacion.objects.filter(
        profesor=profesor, 
        fecha__gte=date.today()
    ).order_by('fecha')[:5]
    
    # Tareas revisadas
    tareas_revisadas = 0  # Por ahora lo dejamos en 0 si aún no existe ese modelo
    
    context = {
        "cursos_activos": cursos_activos,
        "alumnos_inscritos": alumnos_inscritos,
        "tareas_revisadas": tareas_revisadas,
        "material_subido": materiales_subidos,
        "cursos": cursos,
        "evaluaciones": evaluaciones,
    }
    return render(request, "dashboard_profesor.html", context)

@login_required
def profesor_cursos(request):
    """Muestra los cursos creados por el profesor logueado."""
    cursos = Curso.objects.filter(profesor=request.user).order_by("-id")
    return render(request, "profesor_cursos.html", {"cursos": cursos})

@login_required
def profesor_evaluaciones(request):
    evaluaciones = Evaluacion.objects.filter(profesor=request.user).order_by('-fecha')
    return render(request, "profesor_evaluaciones.html", {"evaluaciones": evaluaciones})

@login_required
def profesor_material(request):
    # 🔹 Mostrar materiales del profesor
    materiales = MaterialDidactico.objects.filter(profesor=request.user).order_by('-fecha_subida')
    
    # 🔹 Traer cursos del profesor para el selector
    cursos = Curso.objects.filter(profesor=request.user)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.profesor = request.user
            
            # 🔹 Asociar el curso seleccionado (si existe)
            curso_id = request.POST.get('curso')
            if curso_id:
                try:
                    material.curso = Curso.objects.get(id=curso_id, profesor=request.user)
                except Curso.DoesNotExist:
                    material.curso = None
            
            # 🔹 Detectar tipo automáticamente
            archivo = material.archivo
            if archivo:
                ext = os.path.splitext(archivo.name)[1].lower()
                if ext in ['.pdf']:
                    material.tipo = 'PDF'
                elif ext in ['.ppt', '.pptx']:
                    material.tipo = 'Presentación'
                elif ext in ['.mp4', '.mov', '.avi']:
                    material.tipo = 'Video'
                elif ext in ['.doc', '.docx']:
                    material.tipo = 'Documento'
                else:
                    material.tipo = 'Otro'
            elif material.enlace:
                material.tipo = 'Enlace'
            else:
                material.tipo = 'Otro'
            
            material.save()
            messages.success(request, "✅ Material subido correctamente.")
            return redirect('dashboard:profesor_material')
    else:
        form = MaterialForm()
    
    return render(request, 'profesor_material.html', {
        'form': form,
        'materiales': materiales,
        'cursos': cursos
    })

@login_required
def editar_material_view(request, id):
    material = get_object_or_404(MaterialDidactico, id=id, profesor=request.user)
    if request.method == 'POST':
        material.titulo = request.POST.get('titulo')
        material.tipo = request.POST.get('tipo')
        if request.FILES.get('archivo'):
            material.archivo = request.FILES['archivo']
        material.enlace = request.POST.get('enlace')
        material.save()
        messages.success(request, "✅ Material actualizado correctamente.")
        return redirect('dashboard:profesor_material')
    return render(request, 'editar_material.html', {'material': material})

@login_required
def eliminar_material_view(request, id):
    material = get_object_or_404(MaterialDidactico, id=id, profesor=request.user)
    material.delete()
    messages.success(request, "🗑️ Material eliminado correctamente.")
    return redirect('dashboard:profesor_material')

@login_required
def foros_profesor(request):
    foros = Foro.objects.all().order_by('-fecha_creacion')
    return render(request, 'foros_profesor.html', {'foros': foros})

# ---------------------------
# DASHBOARD: USUARIO (ALUMNO)
# ---------------------------

@login_required
def dashboard_user(request):
    """Vista principal del dashboard para estudiantes con datos dinámicos"""
    alumno = request.user
    
    try:
        # Cursos en los que está inscrito
        cursos_inscritos = Inscripcion.objects.filter(alumno=alumno)
        user_cursos_count = cursos_inscritos.count()
        
        # Recursos totales de esos cursos
        cursos_ids = cursos_inscritos.values_list('curso', flat=True)
        recursos = MaterialDidactico.objects.filter(curso__in=cursos_ids)
        
        # Recursos completados según actividad del usuario
        recursos_completados = UserActivity.objects.filter(
            user=alumno, 
            actividad__icontains="visto material"
        ).count()
        
        # Tiempo de estudio total
        total_minutos = LearningSession.objects.filter(user=alumno).aggregate(
            total=models.Sum('duracion_minutos')
        )['total'] or 0
        tiempo_estudio = round(total_minutos / 60)  # en horas
        
        # Logros obtenidos según evaluaciones completadas
        logros_obtenidos = UserActivity.objects.filter(
            user=alumno,
            actividad__icontains="evaluacion completada"
        ).count()
        
        # Recursos nuevos: materiales que no ha visto
        vistos_ids = UserActivity.objects.filter(
            user=alumno,
            actividad__icontains="visto material"
        ).values_list('curso', flat=True)
        
        # Filtrar IDs válidos
        recursos_vistos_ids = [v for v in vistos_ids if v]
        
        recursos_nuevos = recursos.exclude(id__in=recursos_vistos_ids).count()
        
    except Exception as e:
        # En caso de error, usar valores por defecto
        print(f"Error calculando estadísticas: {e}")
        user_cursos_count = 0
        recursos_completados = 0
        tiempo_estudio = 0
        logros_obtenidos = 0
        recursos_nuevos = 0
    
    context = {
        'user_cursos_count': user_cursos_count,
        'recursos_completados': recursos_completados,
        'tiempo_estudio': tiempo_estudio,
        'logros_obtenidos': logros_obtenidos,
        'recursos_nuevos': recursos_nuevos,
    }
    return render(request, 'dashboard_user.html', context)

@login_required
def progreso_estudiante(request):
    """Vista que muestra el progreso completo del estudiante en sus cursos"""
    alumno = request.user

    # ================================
    # 1. Cursos inscritos
    # ================================
    cursos_inscritos = (
        Inscripcion.objects
        .filter(alumno=alumno)
        .select_related('curso')
    )

    user_cursos_count = cursos_inscritos.count()

    # ================================
    # 2. Recursos completados (videos, lecturas, materiales)
    # ================================
    recursos_completados = UserActivity.objects.filter(
        user=alumno,
        actividad__icontains="visto material"
    ).count()

    # ================================
    # 3. Tiempo total de estudio (en horas)
    # ================================
    total_minutos = LearningSession.objects.filter(
        user=alumno
    ).aggregate(
        total=models.Sum('duracion_minutos')
    )['total'] or 0

    tiempo_estudio = round(total_minutos / 60)

    # ================================
    # 4. Logros (evaluaciones completadas)
    # ================================
    logros_obtenidos = UserActivity.objects.filter(
        user=alumno,
        actividad__icontains="evaluacion completada"
    ).count()

    # ================================
    # 5. ACTIVIDADES / TAREAS / EXÁMENES POR CURSO
    # ================================
    progreso_detallado = []

    for inscripcion in cursos_inscritos:
        curso = inscripcion.curso

        # Total de actividades del curso
        total_actividades = Actividad.objects.filter(curso=curso).count()

        # Actividades completadas por el usuario
        actividades_completadas = UserActivity.objects.filter(
            user=alumno,
            actividad__icontains="actividad completada",
            curso=curso
        ).count()

        # Total de evaluaciones
        total_evaluaciones = Evaluacion.objects.filter(curso=curso).count()

        # Evaluaciones completadas
        evaluaciones_completadas = UserActivity.objects.filter(
            user=alumno,
            actividad__icontains="evaluacion completada",
            curso=curso
        ).count()

        # Total de tareas
        total_tareas = Tarea.objects.filter(curso=curso).count()

        # Tareas entregadas
        tareas_entregadas = UserActivity.objects.filter(
            user=alumno,
            actividad__icontains="tarea entregada",
            curso=curso
        ).count()

        # Cálculo de progreso general
        total_items = total_actividades + total_evaluaciones + total_tareas
        completados = actividades_completadas + evaluaciones_completadas + tareas_entregadas

        progreso_porcentaje = round((completados / total_items) * 100) if total_items > 0 else 0

        progreso_detallado.append({
            "curso": curso,
            "inscripcion": inscripcion,
            "progreso": progreso_porcentaje,
            "total_actividades": total_actividades,
            "actividades_completadas": actividades_completadas,
            "total_evaluaciones": total_evaluaciones,
            "evaluaciones_completadas": evaluaciones_completadas,
            "total_tareas": total_tareas,
            "tareas_entregadas": tareas_entregadas,
        })

    # ================================
    # 6. INSIGNIAS OBTENIDAS
    # ================================
    evaluar_insignias(alumno)  # re-evalúa por si hay nuevas
    insignias_obtenidas = insignias_de(alumno)
    insignias_bloqueadas = [i for i in CATALOGO_INSIGNIAS
                            if i['codigo'] not in [x['codigo'] for x in insignias_obtenidas]]

    # ================================
    # CONTEXTO FINAL
    # ================================
    context = {
        'user_cursos_count': user_cursos_count,
        'recursos_completados': recursos_completados,
        'tiempo_estudio': tiempo_estudio,
        'logros_obtenidos': logros_obtenidos,
        'cursos_inscritos': cursos_inscritos,
        'progreso_detallado': progreso_detallado,
        'insignias_obtenidas': insignias_obtenidas,
        'insignias_bloqueadas': insignias_bloqueadas,
    }

    return render(request, 'progreso_estudiante.html', context)



# ---------------------------
# GESTIÓN DE CURSOS
# ---------------------------

@login_required
def crear_curso(request):
    """Vista para que el profesor cree un nuevo curso."""
    if not request.user.is_staff:
        messages.error(request, "No tienes permiso para crear cursos.")
        return redirect("dashboard_user")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        categoria = request.POST.get("categoria")
        
        if not nombre or not descripcion:
            messages.error(request, "Por favor completa todos los campos.")
            return redirect("crear_curso")
        
        # Crear curso asociado al profesor
        Curso.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            profesor=request.user
        )
        messages.success(request, "📘 Curso creado correctamente.")
        return redirect("dashboard_profesor")
    
    return render(request, "crear_curso.html")

@login_required
def cursos_disponibles(request):
    cursos = Curso.objects.exclude(inscritos__alumno=request.user)
    return render(request, "cursos_disponibles.html", {"cursos": cursos})

@login_required
def inscribirse_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    Inscripcion.objects.get_or_create(alumno=request.user, curso=curso)
    nuevas = evaluar_insignias(request.user)
    if nuevas:
        insignia = next((i for i in CATALOGO_INSIGNIAS if i['codigo'] == nuevas[0]), None)
        if insignia:
            messages.success(request, f"🏆 ¡Nueva insignia desbloqueada: {insignia['nombre']}!")
    messages.success(request, f"✅ Te has inscrito en {curso.nombre}.")
    return redirect('dashboard:detalle_curso', curso_id=curso.id)

@login_required
def mis_recursos(request):
    alumno = request.user

    # Obtener cursos donde el alumno está inscrito
    cursos_ids = Inscripcion.objects.filter(
    alumno=alumno
    ).values_list("curso_id", flat=True)


    # Obtener materiales visibles de esos cursos
    materiales = MaterialDidactico.objects.filter(
    curso_id__in=cursos_ids
    ).order_by("-fecha_subida")

    context = {
        "materiales": materiales
    }

    return render(request, "mis_recursos.html", context)



@login_required
def detalle_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Actividades y tareas del curso
    actividades = Actividad.objects.filter(curso=curso)
    tareas = Tarea.objects.filter(curso=curso)
    
    # Entregas del usuario (solo para marcar si la tarea ya fue entregada)
    entregas_qs = EntregaTarea.objects.filter(alumno=request.user, tarea__curso=curso)
    entregas_dict = {entrega.tarea.id: entrega for entrega in entregas_qs}

    # Solo si es profesor
    if hasattr(request.user, "perfilusuario") and getattr(request.user.perfilusuario, "is_teacher", False):
        materiales = MaterialDidactico.objects.filter(curso=curso)
        alumnos = Inscripcion.objects.filter(curso=curso).select_related('alumno')
        url_volver = reverse('dashboard:profesor_cursos')
    else:
        materiales = []
        alumnos = []
        url_volver = reverse('dashboard:dashboard_user')

    context = {
        "curso": curso,
        "actividades": actividades,
        "tareas": tareas,
        "entregas_dict": entregas_dict,  # 🔹 Esto es clave para mostrar entregas
        "materiales": materiales,
        "alumnos": alumnos,
        "url_volver": url_volver
    }

    return render(request, "detalle_curso.html", context)



@login_required
def editar_curso(request, curso_id):
    """Permite al profesor editar la información de un curso existente."""
    curso = get_object_or_404(Curso, id=curso_id, profesor=request.user)
    
    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ El curso se actualizó correctamente.")
            return redirect("dashboard:profesor_cursos")
    else:
        form = CursoForm(instance=curso)
    
    context = {
        "form": form,
        "curso": curso
    }
    return render(request, "editar_curso.html", context)

@login_required
def asignar_material_a_curso(request, material_id):
    try:
        material = MaterialDidactico.objects.get(id=material_id, profesor=request.user)
    except MaterialDidactico.DoesNotExist:
        messages.error(request, "❌ No se encontró el material.")
        return redirect('profesor_material')
    
    if request.method == 'POST':
        curso_id = request.POST.get('curso')
        try:
            curso = Curso.objects.get(id=curso_id, profesor=request.user)
            material.curso = curso
            material.save()
            messages.success(request, f"✅ Material asignado correctamente al curso {curso.nombre}.")
        except Curso.DoesNotExist:
            messages.error(request, "⚠️ Curso no válido.")
    
    return redirect('profesor_material')

# ---------------------------
# GESTIÓN DE EVALUACIONES
# ---------------------------

@login_required
def crear_evaluacion(request):
    # 🔹 Obtener solo los cursos del profesor actual
    cursos = Curso.objects.filter(profesor=request.user)
    
    if request.method == 'POST':
        form = EvaluacionForm(request.POST)
        if form.is_valid():
            evaluacion = form.save(commit=False)
            evaluacion.profesor = request.user
            evaluacion.save()
            messages.success(request, "✅ Evaluación creada correctamente.")
            return redirect('dashboard:profesor_evaluaciones')
    else:
        form = EvaluacionForm()
    
    # 🔹 Limitar el campo 'curso' a los cursos del profesor logueado
    form.fields['curso'].queryset = cursos
    
    return render(request, 'crear_evaluacion.html', {'form': form, 'cursos': cursos})

@login_required
def editar_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, profesor=request.user)
    cursos = Curso.objects.filter(profesor=request.user)
    
    if request.method == 'POST':
        form = EvaluacionForm(request.POST, instance=evaluacion)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Evaluación actualizada correctamente.")
            return redirect('dashboard:profesor_evaluaciones')
    else:
        form = EvaluacionForm(instance=evaluacion)
        form.fields['curso'].queryset = cursos
    
    return render(request, 'editar_evaluacion.html', {'form': form, 'evaluacion': evaluacion})

@login_required
def eliminar_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, profesor=request.user)
    evaluacion.delete()
    messages.success(request, "🗑️ Evaluación eliminada correctamente.")
    return redirect('dashboard:profesor_evaluaciones')

@login_required
def detalle_evaluacion(request, evaluacion_id):
    """Muestra el detalle de una evaluación y permite agregar materiales del curso"""
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, profesor=request.user)
    curso = evaluacion.curso
    
    # 🔹 Materiales ya asociados a esta evaluación
    materiales_asignados = evaluacion.materiales.all()
    
    # 🔹 Materiales disponibles para agregar (del curso del profesor)
    materiales_disponibles = MaterialDidactico.objects.filter(curso=curso, profesor=request.user)
    
    # 🔹 Agregar material seleccionado a la evaluación
    if request.method == "POST":
        material_id = request.POST.get("material_id")
        if material_id:
            try:
                material = MaterialDidactico.objects.get(id=material_id, curso=curso, profesor=request.user)
                evaluacion.materiales.add(material)
                messages.success(request, f"📘 El material '{material.titulo}' se agregó a la evaluación correctamente.")
            except MaterialDidactico.DoesNotExist:
                messages.error(request, "❌ El material seleccionado no existe o no pertenece a este curso.")
            return redirect("dashboard:detalle_evaluacion", evaluacion_id=evaluacion.id)
    
    context = {
        "evaluacion": evaluacion,
        "curso": curso,
        "materiales_asignados": materiales_asignados,
        "materiales_disponibles": materiales_disponibles,
    }
    return render(request, "detalle_evaluacion.html", context)

@login_required
def quitar_material_evaluacion(request, evaluacion_id, material_id):
    """Elimina la relación entre un material y una evaluación (sin borrar el archivo)."""
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, profesor=request.user)
    try:
        material = evaluacion.materiales.get(id=material_id)
        evaluacion.materiales.remove(material)
        messages.success(request, f"🗑️ El material '{material.titulo}' se quitó de la evaluación.")
    except MaterialDidactico.DoesNotExist:
        messages.error(request, "❌ El material no pertenece a esta evaluación.")
    
    return redirect("detalle_evaluacion", evaluacion_id=evaluacion.id)

# ---------------------------
# APIs y VISTAS DE IA
# ---------------------------

def ai_stats_api(request):
    total_users = User.objects.count()
    total_students = User.objects.filter(groups__name='Alumno').count()
    total_teachers = User.objects.filter(groups__name='Profesor').count()
    total_admins = User.objects.filter(is_staff=True).count()
    
    data = {
        'total_users': total_users,
        'students': total_students,
        'teachers': total_teachers,
        'admins': total_admins
    }
    return JsonResponse(data)

@staff_member_required
def admin_distribution_view(request):
    total_users = User.objects.count()
    students = User.objects.filter(groups__name='Alumno').count()
    teachers = User.objects.filter(groups__name='Profesor').count()
    admins = User.objects.filter(is_staff=True).count()
    
    context = {
        'total_users': total_users,
        'students': students,
        'teachers': teachers,
        'admins': admins
    }
    return render(request, 'admin_dashboard.html', context)

@csrf_exempt
def ai_chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Usa POST.'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'reply': 'Escríbeme tu pregunta 🤖'}, status=200)

    # Si hay OPENAI_API_KEY, delegar en el motor IA real de la app 'ai'
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=[
                    {'role': 'system', 'content': 'Eres el tutor virtual de EduConnect+. Responde en español, conciso y con pasos.'},
                    {'role': 'user', 'content': user_message},
                ],
                max_tokens=400,
                temperature=0.2,
            )
            return JsonResponse({'reply': resp.choices[0].message.content.strip()})
        except Exception:
            pass  # cae al fallback local

    # Fallback local inteligente usando datos reales de la plataforma
    msg = user_message.lower()
    es_profesor = data.get('rol') == 'profesor' or request.user.is_staff
    
    # Datos reales de la BD
    total_cursos = Curso.objects.count()
    cursos_nombres = list(Curso.objects.values_list('nombre', flat=True)[:6])
    mis_cursos_nombres = list(Curso.objects.filter(profesor=request.user).values_list('nombre', flat=True)[:6]) if es_profesor else list(Inscripcion.objects.filter(alumno=request.user).values_list('curso__nombre', flat=True)[:6])
    mis_tareas_pendientes = Tarea.objects.filter(curso__in=Inscripcion.objects.filter(alumno=request.user).values('curso')).count() if not es_profesor else 0
    
    saludo = f"¡Hola {request.user.first_name or request.user.username}! 👋"
    
    if es_profesor:
        if any(p in msg for p in ['hola', 'buenas', 'hey']):
            reply = f"{saludo} Soy tu asistente docente 🤖. Tienes {len(mis_cursos_nombres)} curso(s) a tu cargo. Puedo ayudarte a crear cursos, subir material, crear evaluaciones o revisar el foro. ¿Qué necesitas?"
        elif 'crear' in msg and ('curso' in msg or 'clase' in msg):
            reply = "Para crear un curso: Dashboard → 'Mis Cursos' → 'Crear Curso'. Completa nombre, descripción y categoría. Tus alumnos podrán inscribirse de inmediato desde 'Cursos Disponibles'."
        elif 'material' in msg or 'recurso' in msg or 'subir' in msg:
            reply = "Para subir material: 'Material Didáctico' → completa título, descripción, curso y adjunta el archivo (PDF, PPT, Word, imágenes, videos). Los alumnos lo verán al instante en 'Mis Recursos'."
        elif 'evalua' in msg or 'examen' in msg or 'quiz' in msg:
            reply = "Para crear una evaluación: 'Evaluaciones' → 'Crear Evaluación'. Puedes vincular materiales del curso para que el alumno estudie antes de presentarla."
        elif 'alumn' in msg:
            reply = f"En tus cursos hay inscripciones activas. Entra a cada curso para ver la lista de participantes y su progreso individual. Actualmente tienes {len(mis_cursos_nombres)} curso(s): {', '.join(mis_cursos_nombres) if mis_cursos_nombres else 'ninguno aún — crea tu primero curso 🚀'}"
        elif 'foro' in msg:
            reply = "En el Foro Académico puedes moderar discusiones y fijar temas importantes. Tus alumnos participan ganando insignias 💬"
        elif 'insignia' in msg or 'logro' in msg:
            reply = "Tus alumnos ganan insignias automáticamente: 🎓 por inscribirse, ✍️ por entregar tareas, 💬 por participar en foros. Motívalos a completar actividades para desbloquearlas todas."
        else:
            reply = f"Soy tu asistente docente 🤖. Con {total_cursos} cursos en la plataforma, puedo orientarte sobre: crear cursos 📘, subir material 📤, evaluaciones 📝, foros 💬 y seguimiento de alumnos 👥. ¿Sobre cuál quieres saber más?"
    else:
        if any(p in msg for p in ['hola', 'buenas', 'hey']):
            reply = f"{saludo} Soy tu tutor IA 🤖. {'Estás inscrito en: ' + ', '.join(mis_cursos_nombres) + '. ' if mis_cursos_nombres else ''}¿Quieres recomendaciones de cursos, ayuda con tareas o saber sobre insignias?"
        elif 'recomiend' in msg or 'qué curso' in msg or 'que curso' in msg:
            if cursos_nombres:
                disponibles = [c for c in cursos_nombres if c not in mis_cursos_nombres]
                reply = f"📚 Te recomiendo estos cursos ({len(disponibles)} disponibles para ti): {', '.join(disponibles) if disponibles else 'ya estás inscrito en todos los que hay 😎'}. Ve a 'Cursos Disponibles' en tu menú para inscribirte."
            else:
                reply = "Aún no hay cursos publicados en la plataforma. Pídele a un profesor que cree el primero 🚀"
        elif 'curso' in msg and ('inscri' in msg or 'unir' in msg or 'apuntar' in msg):
            reply = f"Para inscribirte: Dashboard → 'Cursos Disponibles' → botón 'Inscribirme'. {('Cursos actuales: ' + ', '.join(cursos_nombres) + '.') if cursos_nombres else 'Aún no hay cursos publicados.'} Al inscribirte ganas tu primera insignia 🎓"
        elif 'recurso' in msg or 'material' in msg or 'subir' in msg:
            reply = "Para subir un recurso: menú 'Recursos' → 'Subir recurso', completa título, descripción y archivo (PDF, DOCX, imagen...). Los materiales de tus cursos aparecen en 'Mis Recursos'."
        elif 'foro' in msg or 'pregunta' in msg or 'duda' in msg:
            reply = "En el 'Foro' puedes crear publicaciones y responder a tus compañeros. Los profesores pueden fijar temas importantes. ¡Participar suma insignias! 💬"
        elif 'insignia' in msg or 'logro' in msg or 'progreso' in msg:
            reply = "Ganas insignias automáticamente: 🎓 al inscribirte a tu 1er curso, ✍️ al entregar tareas, 💬 por participar en foros. Consulta tu página de 'Mi Progreso' para verlas."
        elif 'tarea' in msg or 'entrega' in msg:
            reply = f"Tienes {mis_tareas_pendientes} tarea(s) en tus cursos. Entra al curso → sección 'Tareas' → botón 'Entregar'. Puedes adjuntar archivo o escribir texto. Tu profesor la calificará con retroalimentación."
        elif 'ayuda' in msg or 'no entiendo' in msg:
            reply = "Te puedo ayudar con: inscribirte a cursos 📚, subir recursos 📤, entregar tareas ✍️, usar el foro 💬 y ganar insignias 🏆. ¿Sobre cuál quieres saber más?"
        else:
            reply = f"Interesante tu pregunta 🤔. {'Tienes ' + str(len(mis_cursos_nombres)) + ' curso(s) activo(s). ' if mis_cursos_nombres else ''}Puedo orientarte sobre cursos, tareas, recursos, foros e insignias. ¿Reformulas o eliges uno de esos temas?"
    
    return JsonResponse({'reply': reply})

@csrf_exempt
def ai_recommendations_api(request):
    """API sencilla de recomendaciones IA."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    role = "Alumno"
    if request.user.groups.filter(name="Profesor").exists():
        role = "Profesor"
    elif request.user.is_staff:
        role = "Administrador"
    
    # Ejemplo de recomendaciones simples
    if role == "Profesor":
        recommendations = [
            "📚 Sube tus materiales didácticos actualizados.",
            "🧠 Usa el chat IA para generar preguntas tipo examen.",
            "📊 Revisa la participación de tus alumnos en clase."
        ]
    elif role == "Alumno":
        recommendations = [
            "🕒 No olvides revisar tus tareas pendientes.",
            "🤖 Usa el chat IA para estudiar temas difíciles.",
            "💡 Participa en los foros para subir tu calificación."
        ]
    else:
        recommendations = [
            "🧭 Administra usuarios desde el panel de control.",
            "📈 Consulta la distribución de usuarios.",
            "🧩 Supervisa las interacciones de IA."
        ]
    
    return JsonResponse({
        'role': role,
        'recommendations': recommendations
    })

@user_passes_test(lambda u: u.is_staff)
def admin_user_distribution(request):
    """Vista para mostrar la distribución de usuarios"""
    total_users = User.objects.count()
    total_staff = User.objects.filter(is_staff=True).count()
    total_professors = User.objects.filter(groups__name='Profesor').count()
    total_students = total_users - total_staff - total_professors
    
    # Datos para Plotly
    data = {
        "labels": ["Administradores", "Profesores", "Alumnos"],
        "values": [total_staff, total_professors, total_students]
    }
    
    context = {
        "data": data,
        "total_users": total_users
    }
    return render(request, "user_distribution.html", context)

@user_passes_test(lambda u: u.is_superuser)
def admin_distribution_plotly_view(request):
    """Vista con gráfica Plotly para distribución de usuarios"""
    users = User.objects.all()
    data = {
        'Tipo': ['Superusuario' if u.is_superuser else 'Staff' if u.is_staff else 'Usuario' for u in users]
    }
    
    df = pd.DataFrame(data)
    fig = px.pie(
        df, 
        names='Tipo',
        title='Distribución de Usuarios en EduConnect',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.3
    )
    fig.update_traces(textinfo='percent+label')
    chart_html = fig.to_html(full_html=False)
    
    return render(request, 'admin_dashboard/distribution.html', {
        'chart_html': chart_html
    })

from django.shortcuts import render, get_object_or_404
from .models import Curso, Actividad, Tarea, EntregaTarea


