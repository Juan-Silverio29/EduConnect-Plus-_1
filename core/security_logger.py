# core/security_logger.py
import logging
from django.utils import timezone

logger = logging.getLogger('security')

def log_intento_registro(ip, username, exito, razon=None):
    """
    Log de intentos de registro para auditoría de seguridad
    """
    timestamp = timezone.now().isoformat()
    estado = "EXITOSO" if exito else "FALLIDO"
    mensaje_razon = f" - Razón: {razon}" if razon else ""
    
    mensaje = f"[SECURITY] Registro {estado} - IP: {ip} - Usuario: {username} - Timestamp: {timestamp}{mensaje_razon}"
    
    if exito:
        logger.info(mensaje)
    else:
        logger.warning(mensaje)

def log_intento_login(ip, username, exito):
    """
    Log de intentos de login para auditoría
    """
    timestamp = timezone.now().isoformat()
    estado = "EXITOSO" if exito else "FALLIDO"
    
    mensaje = f"[SECURITY] Login {estado} - IP: {ip} - Usuario: {username} - Timestamp: {timestamp}"
    
    if exito:
        logger.info(mensaje)
    else:
        logger.warning(mensaje)