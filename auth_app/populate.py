# populate.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User
from auth_app.models import PerfilUsuario

# Crear usuarios de prueba
usuarios = [
    {"username": "admin1", "email": "admin1@test.com", "password": "admin123", "first_name": "Admin", "last_name": "Uno", "is_superuser": True, "is_staff": True},
    {"username": "profesor1", "email": "prof1@test.com", "password": "prof123", "first_name": "Profesor", "last_name": "Uno", "is_superuser": False, "is_staff": True},
    {"username": "estudiante1", "email": "est1@test.com", "password": "est123", "first_name": "Estudiante", "last_name": "Uno", "is_superuser": False, "is_staff": False},
]

for u in usuarios:
    if not User.objects.filter(username=u["username"]).exists():
        user = User.objects.create_user(
            username=u["username"],
            email=u["email"],
            password=u["password"],
            first_name=u["first_name"],
            last_name=u["last_name"],
            is_superuser=u["is_superuser"],
            is_staff=u["is_staff"]
        )
        PerfilUsuario.objects.create(user=user, institucion="Institución X")
        print(f"Usuario {u['username']} creado.")

print("Datos de prueba insertados correctamente.")
