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
