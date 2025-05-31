# finanzas/utils.py - UTILIDADES PAYPAL COMPLETAS
from django.conf import settings
import requests
import base64
import json
import time

def verificar_configuracion_paypal():
    """
    Verifica que toda la configuración de PayPal esté correcta
    """
    print("\n" + "="*60)
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN PAYPAL")
    print("="*60)
    
    # Verificar variables de configuración
    configuracion = {
        'PAYPAL_CLIENT_ID': getattr(settings, 'PAYPAL_CLIENT_ID', None),
        'PAYPAL_CLIENT_SECRET': getattr(settings, 'PAYPAL_CLIENT_SECRET', None),
        'PAYPAL_MODE': getattr(settings, 'PAYPAL_MODE', None),
        'PAYPAL_BASE_URL': getattr(settings, 'PAYPAL_BASE_URL', None),
        'DOMAIN_URL': getattr(settings, 'DOMAIN_URL', None),
    }
    
    print("\n📋 Variables de Configuración:")
    for key, value in configuracion.items():
        if value:
            if 'SECRET' in key:
                print(f"   ✅ {key}: {'*' * 20} (SET)")
            elif 'CLIENT_ID' in key:
                print(f"   ✅ {key}: {value[:15]}... (SET)")
            else:
                print(f"   ✅ {key}: {value}")
        else:
            print(f"   ❌ {key}: NOT SET")
    
    # Verificar que todas las variables estén configuradas
    missing_vars = [key for key, value in configuracion.items() if not value]
    if missing_vars:
        print(f"\n❌ VARIABLES FALTANTES: {', '.join(missing_vars)}")
        return False
    
    print(f"\n✅ Todas las variables están configuradas")
    
    # Test de conectividad con PayPal
    print(f"\n🌐 Probando conectividad con PayPal...")
    return test_paypal_connection()

def test_paypal_connection():
    """
    Prueba la conexión y autenticación con PayPal
    """
    try:
        # Preparar credenciales
        client_id = settings.PAYPAL_CLIENT_ID
        client_secret = settings.PAYPAL_CLIENT_SECRET
        
        if not client_id or not client_secret:
            print(f"   ❌ Credenciales no configuradas")
            return False
        
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # URL de autenticación - USANDO ENDPOINTS CORRECTOS
        auth_url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
        
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {'grant_type': 'client_credentials'}
        
        print(f"   📤 Enviando request a: {auth_url}")
        print(f"   🔐 Usando credenciales: {client_id[:15]}...")
        print(f"   🌍 Modo: {settings.PAYPAL_MODE}")
        
        # Hacer request con timeout
        response = requests.post(
            auth_url, 
            headers=headers, 
            data=data, 
            timeout=settings.PAYPAL_TIMEOUT
        )
        
        print(f"   📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ CONEXIÓN EXITOSA")
            print(f"   🎫 Token obtenido: {token_data.get('access_token', '')[:20]}...")
            print(f"   ⏰ Expira en: {token_data.get('expires_in', 'N/A')} segundos")
            print(f"   🔧 Scope: {token_data.get('scope', 'N/A')[:50]}...")
            
            # Verificar que el token no esté vacío
            if token_data.get('access_token'):
                return True
            else:
                print(f"   ❌ Token vacío recibido")
                return False
        else:
            print(f"   ❌ ERROR DE AUTENTICACIÓN")
            print(f"   📄 Response: {response.text}")
            
            # Diagnóstico específico de errores comunes
            if response.status_code == 401:
                print(f"   🔍 DIAGNÓSTICO: Credenciales incorrectas o modo incorrecto")
                print(f"      - Verifica que las credenciales sean para el modo {settings.PAYPAL_MODE}")
                print(f"      - Sandbox credentials solo funcionan con sandbox endpoint")
                print(f"      - Live credentials solo funcionan con live endpoint")
            elif response.status_code == 403:
                print(f"   🔍 DIAGNÓSTICO: Acceso denegado - cuenta no activada o restringida")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT - PayPal no responde en {settings.PAYPAL_TIMEOUT} segundos")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   🔌 ERROR DE CONEXIÓN - No se puede conectar a PayPal")
        print(f"      - Verifica tu conexión a internet")
        print(f"      - Verifica que el endpoint sea correcto: {settings.PAYPAL_BASE_URL}")
        return False
    except Exception as e:
        print(f"   💥 ERROR INESPERADO: {e}")
        return False
    finally:
        print("="*60 + "\n")

def debug_orden_paypal(orden_data):
    """
    Debug de los datos de una orden antes de enviarla a PayPal
    """
    print("\n" + "="*50)
    print("🔍 DEBUG DE ORDEN PAYPAL")
    print("="*50)
    
    # Validar estructura básica
    required_fields = ['intent', 'purchase_units', 'application_context']
    for field in required_fields:
        if field in orden_data:
            print(f"   ✅ {field}: Present")
        else:
            print(f"   ❌ {field}: Missing")
    
    # Validar purchase_units
    if 'purchase_units' in orden_data and orden_data['purchase_units']:
        pu = orden_data['purchase_units'][0]
        print(f"\n📦 Purchase Unit:")
        print(f"   💰 Amount: {pu.get('amount', {}).get('value', 'N/A')} {pu.get('amount', {}).get('currency_code', 'N/A')}")
        print(f"   📋 Reference ID: {pu.get('reference_id', 'N/A')}")
        print(f"   📝 Description: {pu.get('description', 'N/A')}")
        
        # Validar items
        items = pu.get('items', [])
        print(f"   📦 Items: {len(items)}")
        for i, item in enumerate(items):
            print(f"      {i+1}. {item.get('name', 'N/A')} x{item.get('quantity', 'N/A')} @ {item.get('unit_amount', {}).get('value', 'N/A')}")
    
    # Validar application_context
    if 'application_context' in orden_data:
        ac = orden_data['application_context']
        print(f"\n🔧 Application Context:")
        print(f"   🏠 Brand Name: {ac.get('brand_name', 'N/A')}")
        print(f"   📱 Landing Page: {ac.get('landing_page', 'N/A')}")
        print(f"   🚀 User Action: {ac.get('user_action', 'N/A')}")
        print(f"   📍 Return URL: {ac.get('return_url', 'N/A')}")
        print(f"   ❌ Cancel URL: {ac.get('cancel_url', 'N/A')}")
    
    print("="*50 + "\n")

def get_paypal_config_status():
    """
    Retorna el estado de la configuración PayPal para mostrar en templates
    """
    try:
        config_ok = all([
            getattr(settings, 'PAYPAL_CLIENT_ID', None),
            getattr(settings, 'PAYPAL_CLIENT_SECRET', None),
            getattr(settings, 'PAYPAL_BASE_URL', None),
            getattr(settings, 'PAYPAL_MODE', None)
        ])
        
        return {
            'configured': config_ok,
            'mode': getattr(settings, 'PAYPAL_MODE', 'unknown'),
            'client_id_preview': (settings.PAYPAL_CLIENT_ID[:15] + '...' 
                                 if getattr(settings, 'PAYPAL_CLIENT_ID', None) 
                                 else 'NOT SET'),
            'base_url': getattr(settings, 'PAYPAL_BASE_URL', 'NOT SET'),
            'domain_url': getattr(settings, 'DOMAIN_URL', 'NOT SET')
        }
    except Exception as e:
        print(f"Error getting PayPal config status: {e}")
        return {
            'configured': False,
            'mode': 'unknown',
            'client_id_preview': 'ERROR',
            'base_url': 'ERROR',
            'domain_url': 'ERROR'
        }

def validate_paypal_order_data(order_data):
    """
    Valida que los datos de una orden PayPal sean correctos antes de enviarla
    """
    errors = []
    
    # Validar estructura básica
    if not isinstance(order_data, dict):
        errors.append("Order data debe ser un diccionario")
        return errors
    
    # Validar intent
    if 'intent' not in order_data:
        errors.append("Campo 'intent' es requerido")
    elif order_data['intent'] not in ['CAPTURE', 'AUTHORIZE']:
        errors.append("Intent debe ser 'CAPTURE' o 'AUTHORIZE'")
    
    # Validar purchase_units
    if 'purchase_units' not in order_data:
        errors.append("Campo 'purchase_units' es requerido")
    elif not isinstance(order_data['purchase_units'], list):
        errors.append("purchase_units debe ser una lista")
    elif len(order_data['purchase_units']) == 0:
        errors.append("purchase_units no puede estar vacío")
    else:
        # Validar primer purchase_unit
        pu = order_data['purchase_units'][0]
        
        if 'amount' not in pu:
            errors.append("purchase_unit debe tener 'amount'")
        else:
            amount = pu['amount']
            if 'currency_code' not in amount:
                errors.append("amount debe tener 'currency_code'")
            if 'value' not in amount:
                errors.append("amount debe tener 'value'")
            else:
                try:
                    float(amount['value'])
                except ValueError:
                    errors.append("amount.value debe ser un número válido")
    
    # Validar application_context
    if 'application_context' in order_data:
        ac = order_data['application_context']
        
        # Validar URLs
        for url_field in ['return_url', 'cancel_url']:
            if url_field in ac:
                url = ac[url_field]
                if not url.startswith(('http://', 'https://')):
                    errors.append(f"{url_field} debe ser una URL válida")
    
    return errors

def retry_paypal_request(func, max_retries=3, delay=1):
    """
    Reintentar requests a PayPal en caso de errores temporales
    """
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise
            print(f"   ⏰ Timeout en intento {attempt + 1}, reintentando en {delay}s...")
            time.sleep(delay)
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise
            print(f"   🔌 Error de conexión en intento {attempt + 1}, reintentando en {delay}s...")
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            # Para otros errores de requests, no reintentar
            raise
    
    return None