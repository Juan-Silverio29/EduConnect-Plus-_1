from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Models
from auth_app.models import PerfilUsuario
from dashboard.models import Curso, MaterialDidactico
from forum.models import Foro, Comentario
from resources.models import Recursos

# ==========================
# VISTAS DE API PARA DASHBOARD
# ==========================

@login_required
def ai_stats_api(request):
    """API para estadísticas del dashboard"""
    try:
        # Estadísticas generales
        total_usuarios = User.objects.count()
        total_profesores = User.objects.filter(is_staff=True).count()
        total_estudiantes = User.objects.filter(is_staff=False, is_superuser=False).count()
        
        # Estadísticas del usuario actual
        user_stats = {}
        if request.user.is_staff:
            # Si es profesor
            user_stats['cursos'] = Curso.objects.filter(profesor=request.user).count()
            user_stats['materiales'] = MaterialDidactico.objects.filter(profesor=request.user).count()
            user_stats['evaluaciones'] = 0  # Puedes agregar modelo de evaluaciones
        else:
            # Si es estudiante
            user_stats['cursos'] = Curso.objects.filter(alumnos=request.user).count()
            user_stats['materiales'] = Recursos.objects.filter(completado=True).count()
            user_stats['evaluaciones'] = 0  # Puedes agregar modelo de evaluaciones
        
        return JsonResponse({
            'total_profesores': total_profesores,
            'total_estudiantes': total_estudiantes,
            'total_usuarios': total_usuarios,
            'user_stats': user_stats
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ai_recommendations_api(request):
    """API para recomendaciones personalizadas"""
    try:
        user = request.user
        
        if user.is_staff:
            # Recomendaciones para profesores
            recommendations = [
                {
                    "titulo": "Gestión Avanzada de Cursos",
                    "descripcion": "Aprende técnicas avanzadas para gestionar tus cursos online",
                    "tipo": "Para Profesores",
                    "nivel": "Avanzado"
                },
                {
                    "titulo": "Creación de Material Interactivo",
                    "descripcion": "Herramientas para crear contenido educativo interactivo",
                    "tipo": "Recurso Docente",
                    "nivel": "Intermedio"
                },
                {
                    "titulo": "Evaluaciones Automatizadas",
                    "descripcion": "Implementa sistemas de evaluación automática en tus cursos",
                    "tipo": "Productividad",
                    "nivel": "Intermedio"
                }
            ]
        else:
            # Recomendaciones para estudiantes
            recommendations = [
                {
                    "titulo": "Curso de Python Avanzado",
                    "descripcion": "Perfecciona tus habilidades de programación en Python",
                    "tipo": "Recomendado",
                    "nivel": "Intermedio"
                },
                {
                    "titulo": "Matemáticas para Data Science",
                    "descripcion": "Fundamentos matemáticos esenciales para ciencia de datos",
                    "tipo": "Complementario",
                    "nivel": "Intermedio"
                },
                {
                    "titulo": "Introducción a Machine Learning",
                    "descripcion": "Aprende los conceptos básicos de inteligencia artificial",
                    "tipo": "Trending",
                    "nivel": "Principiante"
                }
            ]
        
        return JsonResponse({
            'recomendaciones': recommendations,
            'user_type': 'profesor' if user.is_staff else 'estudiante'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==========================
# VISTAS DE ADMINISTRACIÓN
# ==========================

@staff_member_required
def admin_user_distribution(request):
    """Vista de administración para distribución de usuarios"""
    # Conteo de usuarios por rol
    profesores = User.objects.filter(is_staff=True, is_superuser=False).count()
    estudiantes = User.objects.filter(is_staff=False, is_superuser=False).count()
    administradores = User.objects.filter(is_superuser=True).count()

    data = {
        'labels': ['Profesores', 'Estudiantes', 'Administradores'],
        'values': [profesores, estudiantes, administradores]
    }

    context = {
        'data': data,
        'total_usuarios': User.objects.count(),
        'total_cursos': Curso.objects.count(),
        'total_materiales': MaterialDidactico.objects.count(),
        'total_foros': Foro.objects.count(),
    }
    return render(request, 'user_distribution.html', context)


# ==========================
# CONFIGURACIÓN DEL ADMIN
# ==========================

from django.contrib.admin import SimpleListFilter

class IsTeacherFilter(SimpleListFilter):
    title = 'Es profesor'
    parameter_name = 'is_teacher'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Sí'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(perfilusuario__is_teacher=True)
        if self.value() == 'no':
            return queryset.filter(perfilusuario__is_teacher=False)
        return queryset

# --------------------------
# Admin para usuarios con perfil
# --------------------------
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'
    readonly_fields = ('foto_preview',)
    fields = ('institucion', 'foto_perfil', 'foto_preview', 'is_teacher')

    def foto_preview(self, obj):
        if obj.foto_perfil:
            return format_html('<img src="{}" width="80" style="border-radius:50%;"/>', obj.foto_perfil.url)
        return "No hay foto"
    foto_preview.short_description = "Vista previa"

class CustomUserAdmin(admin.ModelAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_teacher', 'institucion', 'foto_preview')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'perfilusuario__institucion')
    
    # CORRECCIÓN: Usar el filtro personalizado en lugar de 'perfilusuario__is_teacher'
    list_filter = ('is_staff', 'is_superuser', IsTeacherFilter, 'date_joined')
    
    readonly_fields = ('date_joined', 'last_login')

    def is_teacher(self, obj):
        return obj.perfilusuario.is_teacher if hasattr(obj, 'perfilusuario') else False
    is_teacher.boolean = True
    is_teacher.short_description = 'Profesor'

    def institucion(self, obj):
        return obj.perfilusuario.institucion if hasattr(obj, 'perfilusuario') else "-"
    institucion.short_description = "Institución"

    def foto_preview(self, obj):
        if hasattr(obj, 'perfilusuario') and obj.perfilusuario.foto_perfil:
            return format_html('<img src="{}" width="50" style="border-radius:50%;"/>', obj.perfilusuario.foto_perfil.url)
        return "-"
    foto_preview.short_description = "Foto"

# --------------------------
# Admin de Cursos
# --------------------------
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'grupo', 'profesor', 'numero_alumnos', 'fecha_creacion', 'ver_alumnos')
    search_fields = ('nombre', 'categoria', 'grupo', 'profesor__username', 'descripcion')
    list_filter = ('categoria', 'grupo', 'profesor', 'fecha_creacion')
    readonly_fields = ('fecha_creacion',)
    filter_horizontal = ('alumnos',)

    def numero_alumnos(self, obj):
        return obj.alumnos.count()
    numero_alumnos.short_description = "Alumnos"

    def ver_alumnos(self, obj):
        alumnos = obj.alumnos.all()[:5]  # Mostrar solo los primeros 5
        if alumnos:
            return format_html('<br>'.join([f'👤 {u.get_full_name() or u.username}' for u in alumnos]))
        return "-"
    ver_alumnos.short_description = "Alumnos (primeros 5)"

# --------------------------
# Admin de Material Didáctico
# --------------------------
class MaterialDidacticoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'profesor', 'curso', 'fecha_subida', 'archivo_link', 'archivo_preview')
    search_fields = ('titulo', 'descripcion', 'tipo', 'profesor__username', 'curso__nombre')
    list_filter = ('tipo', 'fecha_subida', 'profesor', 'curso')
    readonly_fields = ('fecha_subida',)

    def archivo_link(self, obj):
        if obj.archivo:
            return format_html('<a href="{}" target="_blank">📎 Descargar</a>', obj.archivo.url)
        elif obj.enlace:
            return format_html('<a href="{}" target="_blank">🔗 Enlace</a>', obj.enlace)
        return "-"
    archivo_link.short_description = "Archivo/Enlace"

    def archivo_preview(self, obj):
        if obj.archivo:
            # Mostrar preview para imágenes
            if obj.archivo.name.lower().endswith(('.jpg', '.png', '.jpeg', '.gif')):
                return format_html('<img src="{}" width="80" style="border-radius:8px;"/>', obj.archivo.url)
            # Icono para otros tipos de archivo
            else:
                return "📄"
        return "-"
    archivo_preview.short_description = "Vista previa"

# --------------------------
# Admin de Foros y Comentarios
# --------------------------
class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 0
    readonly_fields = ('autor', 'fecha')
    fields = ('autor', 'fecha', 'texto', 'archivo')
    show_change_link = True

class ForoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'fecha_creacion', 'numero_comentarios', 'fijado', 'link_foro')
    search_fields = ('titulo', 'descripcion', 'autor__username')
    list_filter = ('fijado', 'fecha_creacion', 'autor')
    inlines = [ComentarioInline]
    readonly_fields = ('fecha_creacion',)
    actions = ['marcar_fijado', 'desmarcar_fijado']

    def numero_comentarios(self, obj):
        return obj.comentarios.count()
    numero_comentarios.short_description = "Comentarios"

    def link_foro(self, obj):
        return format_html('<a href="/admin/forum/foro/{}/change/">📝 Editar</a>', obj.id)
    link_foro.short_description = "Acciones"

    def marcar_fijado(self, request, queryset):
        updated = queryset.update(fijado=True)
        self.message_user(request, f'{updated} foros marcados como fijados.')
    marcar_fijado.short_description = "📌 Marcar como fijado"

    def desmarcar_fijado(self, request, queryset):
        updated = queryset.update(fijado=False)
        self.message_user(request, f'{updated} foros desmarcados como fijados.')
    desmarcar_fijado.short_description = "❌ Desmarcar fijado"

class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('foro', 'autor', 'fecha', 'texto_resumen', 'tiene_archivo')
    search_fields = ('foro__titulo', 'autor__username', 'texto')
    list_filter = ('fecha', 'autor', 'foro')
    readonly_fields = ('fecha',)

    def texto_resumen(self, obj):
        return obj.texto[:100] + ("..." if len(obj.texto) > 100 else "")
    texto_resumen.short_description = "Comentario"

    def tiene_archivo(self, obj):
        return "✅" if obj.archivo else "❌"
    tiene_archivo.short_description = "Archivo"

# --------------------------
# Admin de Recursos
# --------------------------
class RecursosAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'completado', 'fecha_creacion', 'archivo_link', 'archivo_preview')
    search_fields = ('titulo', 'descripcion', 'autor__username')
    list_filter = ('completado', 'fecha_creacion', 'autor')
    readonly_fields = ('fecha_creacion',)
    actions = ['marcar_completado', 'marcar_no_completado']

    def archivo_link(self, obj):
        if obj.archivo:
            return format_html('<a href="{}" target="_blank">📎 Descargar</a>', obj.archivo.url)
        return "-"
    archivo_link.short_description = "Archivo"

    def archivo_preview(self, obj):
        if obj.archivo and obj.archivo.url.lower().endswith(('.jpg','.png','.jpeg','.gif')):
            return format_html('<img src="{}" width="80" style="border-radius:8px;"/>', obj.archivo.url)
        return "-"
    archivo_preview.short_description = "Vista previa"

    def marcar_completado(self, request, queryset):
        updated = queryset.update(completado=True)
        self.message_user(request, f'{updated} recursos marcados como completados.')
    marcar_completado.short_description = "✅ Marcar como completados"

    def marcar_no_completado(self, request, queryset):
        updated = queryset.update(completado=False)
        self.message_user(request, f'{updated} recursos marcados como no completados.')
    marcar_no_completado.short_description = "❌ Marcar como no completados"

# ==========================
# REGISTRO DE MODELOS
# ==========================

# Registrar modelos
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Curso, CursoAdmin)
admin.site.register(MaterialDidactico, MaterialDidacticoAdmin)
admin.site.register(Foro, ForoAdmin)
admin.site.register(Comentario, ComentarioAdmin)
admin.site.register(Recursos, RecursosAdmin)

# ==========================
# PERSONALIZACIÓN DEL ADMIN
# ==========================

# Título del admin
admin.site.site_header = "EduConnect+ - Administración"
admin.site.site_title = "EduConnect+ Admin"
admin.site.index_title = "Panel de Administración"