# apps/tenants/hostname_middleware.py
import logging

logger = logging.getLogger(__name__)

class HostnameDebugMiddleware:
    """
    Middleware para debuggear y forzar el hostname correcto desde headers de proxy.
    DEBE ir ANTES de TenantMainMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener el host del header X-Forwarded-Host si existe
        forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST')
        original_host = request.META.get('HTTP_HOST')
        
        # Si existe X-Forwarded-Host, usarlo
        if forwarded_host:
            request.META['HTTP_HOST'] = forwarded_host
            logger.info(f"🔧 Hostname cambiado: {original_host} → {forwarded_host}")
        else:
            logger.info(f"📡 Hostname original: {original_host}")
        
        # Log adicional para debugging
        logger.info(f"🌐 Request path: {request.path}")
        logger.info(f"🔑 Headers: X-Forwarded-Host={forwarded_host}, HTTP_HOST={request.META.get('HTTP_HOST')}")
        
        response = self.get_response(request)
        return response
