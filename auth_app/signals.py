from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Garantiza que un usuario siempre tenga PerfilUsuario asociado."""
    if not instance:
        return
    PerfilUsuario.objects.update_or_create(
        user=instance,
        defaults={
            'is_teacher': bool(getattr(instance, 'is_staff', False)),
        },
    )
