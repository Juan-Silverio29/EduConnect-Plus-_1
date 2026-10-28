# auth_app/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse

def send_activation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = f"http://{get_current_site(request).domain}/auth/activate/{uid}/{token}/"
    
    send_mail(
        "Activa tu cuenta EduConnect+",
        f"Hola {user.username},\n\nPor favor activa tu cuenta haciendo clic aquí:\n{activation_link}\n\nGracias!",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False
    )



# auth_app/utils.py
from django.http import JsonResponse

def lockout_response(request, credentials):
    """
    Respuesta personalizada cuando un usuario está bloqueado por Axes
    """
    return JsonResponse({
        'error': 'Demasiados intentos fallidos. Tu cuenta ha sido bloqueada temporalmente por 30 minutos. Por favor espera o contacta al administrador.'
    }, status=429)

def get_client_ip(request):
    """
    Obtiene la IP real del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def obtener_estado_intentos(username):
    """
    Obtiene el estado de intentos de un usuario
    """
    from axes.models import AccessAttempt
    
    try:
        attempt = AccessAttempt.objects.filter(username=username).first()
        if attempt:
            intentos_fallidos = attempt.failures_since_start
            intentos_restantes = 5 - intentos_fallidos
            bloqueado = intentos_fallidos >= 5
            
            return {
                'intentos_fallidos': intentos_fallidos,
                'intentos_restantes': intentos_restantes,
                'bloqueado': bloqueado,
                'ultimo_intento': attempt.attempt_time
            }
    except Exception as e:
        print(f"Error obteniendo intentos: {e}")
    
    return {
        'intentos_fallidos': 0,
        'intentos_restantes': 5, 
        'bloqueado': False
    }