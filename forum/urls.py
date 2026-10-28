# forum/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.foro_lista, name="foros"),
    path("crear/", views.crear_foro, name="crear_foro"),
    path("<int:foro_id>/", views.foro_detalle, name="foro_detalle"),
    path("<int:foro_id>/editar/", views.editar_foro, name="editar_foro"),
    path("<int:foro_id>/eliminar/", views.eliminar_foro, name="eliminar_foro"),

    path("comentario/<int:comentario_id>/editar/", views.editar_comentario, name="editar_comentario"),
    path("comentario/<int:comentario_id>/eliminar/", views.eliminar_comentario, name="eliminar_comentario"),
    path('<int:foro_id>/fijar/', views.fijar_foro, name='fijar_foro'),
]
