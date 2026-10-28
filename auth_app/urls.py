# auth_app/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordChangeView 

urlpatterns = [
    # Vistas normales
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("privacy/", views.privacy_policy_view, name="privacy_policy"),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('editar_perfil/', views.editar_perfil_view, name='editar_perfil'),
    path("eliminar_cuenta/", views.eliminar_cuenta, name="eliminar_cuenta"),
    path('configuracion_profesor/', views.configuracion_profesor_view, name='configuracion_profesor'),

    # Cambio de contraseña
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='password_change_done.html'
    ), name='password_change_done'),

    # Dashboards por rol
    path("dashboard/", views.dashboard, name="dashboard"),  # redirige según rol
    path("dashboard/estudiante/", views.estudiante_dashboard, name="dashboard_user"),
    path("dashboard/profesor/", views.profesor_dashboard, name="dashboard_profesor"),
    path("dashboard/admin/", views.admin_dashboard, name="dashboard_admin"),
    path("dashboard/admin/cursos/", views.admin_cursos, name="admin_cursos"),
    path("dashboard/admin/usuarios/", views.admin_usuarios, name="admin_usuarios"),
    path("dashboard/admin/estadisticas/", views.admin_estadisticas, name="admin_estadisticas"),

    # API JWT
    path("api/login/", views.api_login, name="api_login"),
    path("api/register/", views.api_register, name="api_register"),

    # API + sesión Django
    path("api/login_session/", views.api_login_session, name="api_login_session"),
    path("api/register_session/", views.api_register_session, name="api_register_session"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # API
    path("api/register_session/", views.api_register_session, name="api_register_session"),
    path("api/login_session/", views.api_login_session, name="api_login_session"),
     path('api/verificar_intentos/<str:username>/', views.verificar_intentos, name='verificar_intentos'),
]
