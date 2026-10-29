from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Lista usuarios y el rol sugerido con base en Groups y auth_perfil, sin escribir en la base.'

    def handle(self, *args, **options):
        self.stdout.write('id|username|is_staff|is_superuser|groups|is_teacher|role_sugerido')

        for user in User.objects.select_related('auth_perfil').prefetch_related('groups').order_by('id'):
            groups = ','.join(sorted(group.name for group in user.groups.all())) or '[]'
            perfil = getattr(user, 'auth_perfil', None)
            legacy_teacher = getattr(perfil, 'is_teacher', None)

            if user.is_superuser:
                role = 'administrador'
            elif user.groups.filter(name='Administrador').exists():
                role = 'administrador'
            elif user.groups.filter(name='Responsable de capacitación').exists():
                role = 'responsable de capacitación'
            elif user.groups.filter(name='Supervisor').exists():
                role = 'supervisor'
            elif user.groups.filter(name='Colaborador').exists():
                role = 'colaborador'
            elif legacy_teacher is True or user.is_staff:
                role = 'legacy_profesor'
            else:
                role = 'legacy_estudiante'

            self.stdout.write(
                f"{user.id}|{user.username}|{user.is_staff}|{user.is_superuser}|{groups}|{legacy_teacher}|{role}"
            )
