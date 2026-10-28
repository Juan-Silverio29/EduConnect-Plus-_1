# resources/templates/*.html usan nombres SIN namespace ({% url 'lista_recursos' %}),
# pero resources/views.py redirige CON namespace ('resources:lista_recursos').
# Para compatibilidad con ambos, registramos app_name pero dejamos las URLs
# accesibles también sin namespace: incluimos el app dos veces es innecesario;
# la solución simple es que las vistas redirijan SIN namespace.
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_recursos, name="lista_recursos"),
    path('subir/', views.subir_recurso, name="subir_recurso"),
    path('logros/', views.logros_recursos_completados, name="logros_recursos_completados"),
    path("lista/", views.lista_recursos, name="lista_recursos"),
    path("editar/<int:recurso_id>/", views.editar_recurso, name="editar_recurso"),
    path("eliminar/<int:recurso_id>/", views.eliminar_recurso, name="eliminar_recurso"),
    path("cursos/", views.lista_cursos, name="lista_cursos"),
    path("cursos/inscribirse/<int:curso_id>/", views.inscribirse_curso, name="inscribirse_curso"),
    path('cursos/baja/<int:curso_id>/', views.darse_baja_curso, name='darse_baja_curso'),
]
