from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import PerfilUsuario
from .permissions import ROLES


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Garantiza que un usuario siempre tenga PerfilUsuario asociado.

    Solo actúa al crear el User (created=True). No sobrescribe is_teacher
    en updates posteriores (last_login, refresh_from_db, etc.), que antes
    pisaban el valor establecido explícitamente.
    """
    if not instance or not created:
        return
    PerfilUsuario.objects.get_or_create(
        user=instance,
        defaults={
            'is_teacher': bool(getattr(instance, 'is_staff', False)),
        },
    )


@receiver(m2m_changed, sender=User.groups.through)
def prevent_multiple_role_groups(sender, instance, action, reverse, pk_set, **kwargs):
    """Evita que un usuario pertenezca a más de un grupo de rol."""
    if action != 'pre_add' or not pk_set:
        return

    if not reverse:  # user.groups.add(...)
        nuevos = set(Group.objects.filter(pk__in=pk_set, name__in=ROLES).values_list('name', flat=True))
        actuales = set(instance.groups.filter(name__in=ROLES).values_list('name', flat=True))
        if len(nuevos | actuales) > 1:
            raise ValidationError('Un usuario no puede pertenecer a más de un grupo de rol.')
    else:  # grupo.user_set.add(...)
        if instance.name not in ROLES:
            return
        for user in User.objects.filter(pk__in=pk_set):
            if user.groups.filter(name__in=ROLES).exclude(pk=instance.pk).exists():
                raise ValidationError('Un usuario no puede pertenecer a más de un grupo de rol.')
