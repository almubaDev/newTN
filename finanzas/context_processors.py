# finanzas/context_processors.py
from django.conf import settings

def paypal_settings(request):
    """
    Context processor para hacer disponibles las configuraciones de PayPal en templates
    """
    return {
        'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID,
        'PAYPAL_MODE': settings.PAYPAL_MODE,
    }