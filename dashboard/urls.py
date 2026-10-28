# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboards principales
    path('', views.dashboard_view, name='dashboard'),
    path('user/', views.dashboard_user, name='dashboard_user'),
    path('profesor/', views.dashboard_profesor, name='dashboard_profesor'),
    path('admin/', views.dashboard_admin, name='dashboard_admin'),

    # Admin
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin/cursos/', views.admin_cursos, name='admin_cursos'),
    path('admin/estadisticas/', views.admin_estadisticas, name='admin_estadisticas'),
    path('admin/distribucion/', views.admin_user_distribution, name='admin_user_distribution'),

    # Profesor - Cursos
    path('profesor/cursos/', views.profesor_cursos, name='profesor_cursos'),
    path('profesor/crear-curso/', views.crear_curso, name='crear_curso'),
    path('profesor/curso/<int:curso_id>/', views.detalle_curso, name='detalle_curso'),
    path('profesor/editar-curso/<int:curso_id>/', views.editar_curso, name='editar_curso'),

    # Profesor - Evaluaciones
    path('profesor/evaluaciones/', views.profesor_evaluaciones, name='profesor_evaluaciones'),
    path('profesor/crear-evaluacion/', views.crear_evaluacion, name='crear_evaluacion'),
    path('profesor/editar-evaluacion/<int:evaluacion_id>/', views.editar_evaluacion, name='editar_evaluacion'),
    path('profesor/eliminar-evaluacion/<int:evaluacion_id>/', views.eliminar_evaluacion, name='eliminar_evaluacion'),
    path('profesor/evaluacion/<int:evaluacion_id>/', views.detalle_evaluacion, name='detalle_evaluacion'),
    path('profesor/evaluacion/<int:evaluacion_id>/quitar-material/<int:material_id>/', views.quitar_material_evaluacion, name='quitar_material_evaluacion'),

    # Profesor - Material
    path('profesor/material/', views.profesor_material, name='profesor_material'),
    path('profesor/material/editar/<int:id>/', views.editar_material_view, name='editar_material'),
    path('profesor/material/eliminar/<int:id>/', views.eliminar_material_view, name='eliminar_material'),
    path('profesor/material/asignar/<int:material_id>/', views.asignar_material_a_curso, name='asignar_material_a_curso'),

    # Profesor - Foros
    path('profesor/foros/', views.foros_profesor, name='foros_profesor'),

    # Alumno
    path('alumno/cursos-disponibles/', views.cursos_disponibles, name='cursos_disponibles'),
    path('alumno/inscribirse/<int:curso_id>/', views.inscribirse_curso, name='inscribirse_curso'),
    path('curso/<int:curso_id>/', views.detalle_curso, name='detalle_curso'),

    # 🟩 ESTA ES LA ÚNICA RUTA CORRECTA PARA MIS RECURSOS
    path('alumno/mis-recursos/', views.mis_recursos, name='mis_recursos'),

    # Progreso / Logros del estudiante
    # Progreso / Logros del estudiante
    path('progreso/', views.progreso_estudiante, name='progreso'),
    path('progreso/logros/', views.progreso_estudiante, name='logros_recursos_completados'),


    # APIs
    path('api/ai-stats/', views.ai_stats_api, name='ai_stats_api'),
    path('api/ai-chat/', views.ai_chat_api, name='ai_chat_api'),
    path('api/ai-recommendations/', views.ai_recommendations_api, name='ai_recommendations_api'),
]
