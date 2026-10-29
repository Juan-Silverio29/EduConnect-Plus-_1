# auth_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auth_perfil')
    institucion = models.CharField(max_length=150, blank=True, null=True)
    alias = models.CharField(max_length=50, blank=True, null=True)
    semestre = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True, default='img/default_user.png')
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


def user_es_profesor(user):
    """Devuelve True si el usuario debe comportarse como profesor.
    Se toma en cuenta tanto `is_staff` como el perfil `is_teacher` para soportar
    usuarios antiguos sin perfil o perfiles desincronizados.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfilusuario', None)
    if perfil:
        return bool(perfil.is_teacher) or bool(user.is_staff)
    return bool(user.is_staff)
