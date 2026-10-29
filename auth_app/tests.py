import os
import tempfile
from pathlib import Path
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.core.management import call_command
from django.db import connections, transaction
from django.db.backends.sqlite3.base import DatabaseWrapper
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

from auth_app.models import PerfilUsuario, user_es_profesor
from auth_app.permissions import (
    ADMINISTRADOR,
    COLABORADOR,
    RESPONSABLE_CAPACITACION,
    SUPERVISOR,
    get_primary_role,
    has_role,
    roles_de,
)
from dashboard.models import Curso, PerfilUsuario as DashboardPerfil


class AuthCharacterizationTests(TestCase):
    """Pruebas mínimas de caracterización para registrar comportamiento actual."""

    def test_teacher_without_staff_can_see_professor_block(self):
        teacher = User.objects.create_user(
            username='teacher_char',
            email='teacher_char@example.com',
            password='Passw0rd!',
            is_staff=False,
        )
        PerfilUsuario.objects.update_or_create(user=teacher, defaults={'is_teacher': True})
        curso = Curso.objects.create(
            nombre='Curso de prueba',
            descripcion='Curso de validación',
            profesor=teacher,
            grupo='A',
        )

        self.client.force_login(teacher)
        response = self.client.get(reverse('dashboard:detalle_curso_alumno', args=[curso.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '👨‍🎓 Alumnos inscritos')

    def test_user_es_profesor_superuser(self):
        user = User.objects.create_superuser(username='admin_role', email='admin_role@example.com', password='Passw0rd!')
        self.assertTrue(user_es_profesor(user))

    def test_user_es_profesor_is_teacher(self):
        user = User.objects.create_user(username='teacher_role', email='teacher_role@example.com', password='Passw0rd!')
        PerfilUsuario.objects.update_or_create(user=user, defaults={'is_teacher': True})
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user_es_profesor(user))

    def test_user_es_profesor_is_staff(self):
        user = User.objects.create_user(username='staff_role', email='staff_role@example.com', password='Passw0rd!', is_staff=True)
        self.assertTrue(user_es_profesor(user))

    def test_user_es_profesor_without_profile_and_without_staff(self):
        user = User.objects.create_user(username='student_role', email='student_role@example.com', password='Passw0rd!')
        self.assertFalse(user_es_profesor(user))

    def test_admin_filter_on_perfilusuario_raises_field_error(self):
        # CARACTERIZACIÓN: filtro legacy con related_name incorrecto
        with self.assertRaises(FieldError):
            list(User.objects.filter(perfilusuario__is_teacher=True))

    def test_login_student_redirects_to_dashboard_user(self):
        user = User.objects.create_user(
            username='student_char',
            email='student_char@example.com',
            password='Passw0rd!',
            is_staff=False,
        )
        PerfilUsuario.objects.update_or_create(user=user, defaults={'is_teacher': False})

        response = self.client.post('/auth/login/', {
            'username': 'student_char',
            'password': 'Passw0rd!',
        }, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dashboard/user/')

    def test_login_teacher_redirects_to_dashboard_profesor(self):
        user = User.objects.create_user(
            username='teacher_char_2',
            email='teacher_char_2@example.com',
            password='Passw0rd!',
            is_staff=True,
        )
        PerfilUsuario.objects.update_or_create(user=user, defaults={'is_teacher': True})

        response = self.client.post('/auth/login/', {
            'username': 'teacher_char_2',
            'password': 'Passw0rd!',
        }, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dashboard/profesor/')

    def test_register_creates_auth_profile_only(self):
        response = self.client.post('/auth/register/', {
            'username': 'nuevo_usuario',
            'email': 'nuevo_usuario@example.com',
            'password1': 'Passw0rd!',
            'password2': 'Passw0rd!',
            'rol': 'estudiante',
            'nombre': 'Nuevo',
            'apellido': 'Usuario',
            'institucion': 'Empresa',
        }, follow=False)

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='nuevo_usuario')
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())
        self.assertEqual(DashboardPerfil.objects.filter(user=user).count(), 0)

    def test_auth_api_register_creates_profile(self):
        response = self.client.post('/auth/api/register/', {
            'username': 'api_registro',
            'email': 'api_registro@example.com',
            'password1': 'Passw0rd!',
            'password2': 'Passw0rd!',
            'rol': 'estudiante',
            'first_name': 'Api',
            'last_name': 'Registro',
        }, follow=False)

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='api_registro')
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())

    def test_auth_api_login_valid_user_returns_tokens(self):
        user = User.objects.create_user(
            username='api_user',
            email='api_user@example.com',
            password='Passw0rd!',
            is_staff=False,
        )
        PerfilUsuario.objects.update_or_create(user=user, defaults={'is_teacher': False})

        response = self.client.post('/auth/api/login/', {
            'username': 'api_user',
            'password': 'Passw0rd!',
        }, follow=False)

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    def test_createsuperuser_builds_profile_without_integrity_error(self):
        user = User.objects.create_superuser(
            username='superuser_profile',
            email='superuser_profile@example.com',
            password='Passw0rd!',
        )
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())

    def test_api_auth_login_route_does_not_exist(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'missing',
            'password': 'missing',
        }, follow=False)

        self.assertEqual(response.status_code, 404)

    def test_api_login_route_is_protected_and_requires_credentials(self):
        response = self.client.post('/api/login/', {
            'username': 'bad',
            'password': 'wrong',
        }, follow=False)

        self.assertEqual(response.status_code, 401)

    def test_anonymous_dashboard_user_redirects_to_login(self):
        response = self.client.get('/dashboard/user/', follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)

    def test_dashboard_admin_user_list_opens_without_field_error(self):
        admin = User.objects.create_superuser(
            username='admin_filter_check',
            email='admin_filter_check@example.com',
            password='Passw0rd!'
        )
        self.client.force_login(admin)

        response = self.client.get('/admin/auth/user/?is_teacher=yes')

        self.assertEqual(response.status_code, 200)


class AuthPermissionsTests(TestCase):
    def test_get_primary_role_without_group(self):
        user = User.objects.create_user(username='no_role_user', password='Passw0rd!')
        self.assertIsNone(get_primary_role(user))

    def test_get_primary_role_for_each_role(self):
        for nombre in [
            ADMINISTRADOR,
            RESPONSABLE_CAPACITACION,
            SUPERVISOR,
            COLABORADOR,
        ]:
            user = User.objects.create_user(username=f'role_{nombre.lower().replace(" ", "_")}', password='Passw0rd!')
            user.groups.add(Group.objects.get_or_create(name=nombre)[0])
            self.assertEqual(get_primary_role(user), nombre)
            self.assertTrue(has_role(user, nombre))
            self.assertEqual(roles_de(user), [nombre])

    def test_get_primary_role_for_superuser(self):
        user = User.objects.create_superuser(username='super_role_user', email='super_role_user@example.com', password='Passw0rd!')
        self.assertEqual(get_primary_role(user), ADMINISTRADOR)
        self.assertTrue(has_role(user, ADMINISTRADOR))

    def test_get_primary_role_raises_for_two_role_groups(self):
        user = User.objects.create_user(username='two_roles_user', password='Passw0rd!')
        admin_g = Group.objects.get_or_create(name=ADMINISTRADOR)[0]
        sup_g = Group.objects.get_or_create(name=SUPERVISOR)[0]
        User.groups.through.objects.bulk_create([
            User.groups.through(user_id=user.pk, group_id=admin_g.pk),
            User.groups.through(user_id=user.pk, group_id=sup_g.pk),
        ])

        with self.assertRaises(ValueError):
            get_primary_role(user)

    def test_signal_rejects_second_role_group(self):
        user = User.objects.create_user(username='signal_role_user', password='Passw0rd!')
        admin_g = Group.objects.get_or_create(name=ADMINISTRADOR)[0]
        sup_g = Group.objects.get_or_create(name=SUPERVISOR)[0]

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                user.groups.add(admin_g, sup_g)

    def test_signal_rejects_second_role_group_from_group_side(self):
        user = User.objects.create_user(username='group_side_signal_user', password='Passw0rd!')
        admin_g = Group.objects.get_or_create(name=ADMINISTRADOR)[0]
        sup_g = Group.objects.get_or_create(name=SUPERVISOR)[0]
        user.groups.add(admin_g)

        with self.assertRaises(ValidationError):
            sup_g.user_set.add(user)

    def test_signal_allows_non_role_group_addition(self):
        user = User.objects.create_user(username='non_role_signal_user', password='Passw0rd!')
        admin_g = Group.objects.get_or_create(name=ADMINISTRADOR)[0]
        other_g = Group.objects.get_or_create(name='Otro')[0]
        user.groups.add(admin_g)

        other_g.user_set.add(user)
        self.assertIn(other_g, user.groups.all())


class AuthMigrationRoundTripTests(TransactionTestCase):
    serialized_rollback = True
    nombres = ['Administrador', 'Responsable de capacitación', 'Supervisor', 'Colaborador']

    def contar(self):
        return Group.objects.filter(name__in=self.nombres).count()

    def test_ida_y_vuelta(self):
        try:
            call_command('migrate', 'auth_app', '0001', verbosity=0)
            call_command('migrate', 'auth_app', '0002', verbosity=0)
            self.assertEqual(self.contar(), 4)
        finally:
            call_command('migrate', verbosity=0)

