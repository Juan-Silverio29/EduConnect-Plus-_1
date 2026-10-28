from django.contrib.auth.models import User
from dashboard.models import Curso, PerfilUsuario

def create_users():
    """
    Crea usuarios de prueba (profesores y alumnos)
    """
    profesores_data = [
        {"username": "profesor1", "email": "profesor1@educonnect.com", "password": "1234", "is_teacher": True, "institucion": "CUCEI"},
        {"username": "profesor2", "email": "profesor2@educonnect.com", "password": "1234", "is_teacher": True, "institucion": "CUCEI"},
    ]

    alumnos_data = [
        {"username": "alumno1", "email": "alumno1@educonnect.com", "password": "1234", "is_teacher": False, "institucion": "CUCEI"},
        {"username": "alumno2", "email": "alumno2@educonnect.com", "password": "1234", "is_teacher": False, "institucion": "CUCEI"},
        {"username": "alumno3", "email": "alumno3@educonnect.com", "password": "1234", "is_teacher": False, "institucion": "CUCEI"},
    ]

    # Crear profesores
    for data in profesores_data:
        user, created = User.objects.get_or_create(username=data["username"], defaults={"email": data["email"]})
        if created:
            user.set_password(data["password"])
            user.save()
            PerfilUsuario.objects.create(user=user, institucion=data["institucion"], is_teacher=data["is_teacher"])
            print(f"✅ Profesor creado: {user.username}")
        else:
            print(f"ℹ️ Profesor ya existía: {user.username}")

    # Crear alumnos
    for data in alumnos_data:
        user, created = User.objects.get_or_create(username=data["username"], defaults={"email": data["email"]})
        if created:
            user.set_password(data["password"])
            user.save()
            PerfilUsuario.objects.create(user=user, institucion=data["institucion"], is_teacher=data["is_teacher"])
            print(f"✅ Alumno creado: {user.username}")
        else:
            print(f"ℹ️ Alumno ya existía: {user.username}")


def create_cursos():
    """
    Crea cursos de prueba y los asigna a profesores.
    """
    cursos_data = [
        {"nombre": "Matemáticas I", "grupo": "1A", "descripcion": "Curso básico de matemáticas"},
        {"nombre": "Historia Universal", "grupo": "2B", "descripcion": "Repaso de eventos históricos clave"},
        {"nombre": "Física", "grupo": "1A", "descripcion": "Introducción a la física"},
        {"nombre": "Química", "grupo": "2B", "descripcion": "Principios de química general"},
    ]

    # ⚠️ Cambiado related_name para PerfilUsuario
    profesores = User.objects.filter(dashboard_perfil__is_teacher=True)
    alumnos = User.objects.filter(dashboard_perfil__is_teacher=False)

    if not profesores.exists():
        print("⚠️ No hay profesores. Ejecuta primero create_users().")
        return

    for i, data in enumerate(cursos_data):
        profesor = profesores[i % len(profesores)]
        curso, created = Curso.objects.get_or_create(
            nombre=data["nombre"],
            grupo=data["grupo"],
            defaults={
                "descripcion": data["descripcion"],
                "profesor": profesor
            }
        )
        # Asignar todos los alumnos al curso
        curso.alumnos.set(alumnos)
        curso.save()
        print(f"✅ Curso {'creado' if created else 'actualizado'}: {curso.nombre} (Profesor: {profesor.username})")

    print("🎉 Cursos creados o actualizados correctamente.")
