# core/urls.py
"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),         # Página principal
    path('auth/', include('auth_app.urls')),   # Login y Registro
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),  # namespace único
    path("resources/", include("resources.urls")),
    path("forum/", include("forum.urls")),
    path('api/', include('auth_app.api_urls')),
    path('ai/', include('ai.urls')),  # Motor IA (chat, historial, stats)

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

