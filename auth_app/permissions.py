from __future__ import annotations

from django.contrib.auth.models import User

ADMINISTRADOR = 'Administrador'
RESPONSABLE_CAPACITACION = 'Responsable de capacitación'
SUPERVISOR = 'Supervisor'
COLABORADOR = 'Colaborador'

ROLES = [
    ADMINISTRADOR,
    RESPONSABLE_CAPACITACION,
    SUPERVISOR,
    COLABORADOR,
]


def roles_de(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return []
    if getattr(user, 'is_superuser', False):
        return [ADMINISTRADOR]
    return list(user.groups.filter(name__in=ROLES).values_list('name', flat=True))


def get_primary_role(user):
    if user and getattr(user, 'is_superuser', False):
        return ADMINISTRADOR

    grupos = roles_de(user)
    if not grupos:
        return None

    roles_unicos = list(dict.fromkeys(grupos))
    if len(roles_unicos) > 1:
        raise ValueError('El usuario no puede pertenecer a más de un grupo de rol.')

    return roles_unicos[0]


def has_role(user, nombre):
    if user and getattr(user, 'is_superuser', False):
        return nombre == ADMINISTRADOR
    return nombre in roles_de(user)
