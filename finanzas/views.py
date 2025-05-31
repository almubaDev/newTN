# finanzas/views.py - SERVICIOS PAYPAL CORREGIDOS
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Sum, Count, Q, Avg, DecimalField
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
import json
import requests
import uuid
from decimal import Decimal
import logging
import base64
import time

from .models import Carrito, ItemCarrito, OrdenCompra, ItemOrden, LogWebhookPayPal
from tienda.models import TarotProduct
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

# Configurar logging
logger = logging.getLogger(__name__)

# ============== VISTAS EXISTENTES DEL CARRITO ============== #

@login_required
def ver_carrito(request):
    """
    Vista principal del carrito
    """
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.select_related('producto', 'producto__mazo', 'producto__mazo__set').all()
    
    context = {
        'title': 'Mi Carrito de Compras',
        'carrito': carrito,
        'items': items,
    }
    
    return render(request, 'finanzas/carrito.html', context)

@login_required
@require_POST
def agregar_al_carrito(request, producto_id):
    """
    Agregar producto al carrito (AJAX)
    """
    try:
        producto = get_object_or_404(TarotProduct, id=producto_id, estado='activo')
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        
        # Verificar si el producto ya está en el carrito
        item, item_created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 1}
        )
        
        if not item_created:
            # Si ya existe, incrementar cantidad
            item.cantidad = F('cantidad') + 1
            item.save()
            item.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': f'{producto.mazo.nombre} agregado al carrito',
            'total_items': carrito.total_items,
            'item_cantidad': item.cantidad,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar al carrito: {str(e)}'
        })

@login_required
@require_POST
def actualizar_cantidad(request, item_id):
    """
    Actualizar cantidad de un item en el carrito (AJAX)
    """
    try:
        data = json.loads(request.body)
        nueva_cantidad = int(data.get('cantidad', 1))
        
        if nueva_cantidad < 1:
            return JsonResponse({
                'success': False,
                'message': 'La cantidad debe ser mayor a 0'
            })
        
        item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
        item.cantidad = nueva_cantidad
        item.save()
        
        carrito = item.carrito
        
        return JsonResponse({
            'success': True,
            'message': 'Cantidad actualizada',
            'subtotal_item': float(item.subtotal),
            'total_carrito': float(carrito.total),
            'total_items': carrito.total_items,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar: {str(e)}'
        })

@login_required
@require_POST
def eliminar_del_carrito(request, item_id):
    """
    Eliminar producto del carrito (AJAX)
    """
    try:
        item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
        producto_nombre = item.producto.mazo.nombre
        carrito = item.carrito
        
        item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{producto_nombre} eliminado del carrito',
            'total_carrito': float(carrito.total),
            'total_items': carrito.total_items,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar: {str(e)}'
        })

@login_required
@require_POST
def limpiar_carrito(request):
    """
    Vaciar completamente el carrito
    """
    try:
        carrito = get_object_or_404(Carrito, usuario=request.user)
        carrito.limpiar()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Carrito vaciado exitosamente'
            })
        else:
            messages.success(request, 'Carrito vaciado exitosamente')
            return redirect('finanzas:ver_carrito')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error al vaciar carrito: {str(e)}'
            })
        else:
            messages.error(request, f'Error al vaciar carrito: {str(e)}')
            return redirect('finanzas:ver_carrito')

@login_required
def resumen_checkout(request):
    """
    Vista de resumen antes del checkout
    """
    carrito = get_object_or_404(Carrito, usuario=request.user)
    
    if not carrito.items.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('finanzas:ver_carrito')
    
    items = carrito.items.select_related('producto', 'producto__mazo').all()
    
    context = {
        'title': 'Resumen de Compra',
        'carrito': carrito,
        'items': items,
    }
    
    return render(request, 'finanzas/checkout.html', context)

# Widget para mostrar carrito en otras páginas
@login_required
def carrito_widget(request):
    """
    Vista AJAX para widget del carrito en navbar
    """
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        return JsonResponse({
            'total_items': carrito.total_items,
            'total': float(carrito.total),
        })
    except Carrito.DoesNotExist:
        return JsonResponse({
            'total_items': 0,
            'total': 0.0,
        })


# ============== SERVICIO PAYPAL COMPLETO ============== #

class PayPalService:
    """
    Servicio PayPal completo con autenticación y gestión de órdenes
    """
    
    @staticmethod
    def get_access_token():
        """
        Obtiene token de acceso de PayPal usando Client Credentials
        """
        try:
            print(f"🔐 Obteniendo token de PayPal...")
            print(f"   Mode: {settings.PAYPAL_MODE}")
            print(f"   Base URL: {settings.PAYPAL_BASE_URL}")
            
            # Verificar configuración
            if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
                print(f"   ❌ Configuración PayPal incompleta")
                return None
            
            # Crear credenciales básicas
            credentials = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # URL del endpoint de autenticación
            url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            print(f"   📤 Solicitando token...")
            response = requests.post(url, headers=headers, data=data, timeout=15)
            
            print(f"   📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                print(f"   ✅ Token obtenido exitosamente")
                return access_token
            else:
                print(f"   ❌ Error obteniendo token: {response.text}")
                logger.error(f"Error PayPal auth: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"   💥 Error de conexión: {e}")
            logger.error(f"Error de conexión PayPal auth: {e}")
            return None
        except Exception as e:
            print(f"   💥 Error inesperado: {e}")
            logger.error(f"Error inesperado PayPal auth: {e}")
            return None
    
    @staticmethod
    def crear_orden_paypal(orden_compra, request=None):
        """
        Crear orden PayPal - VERSIÓN CORREGIDA
        """
        print(f"\n💰 === CREANDO ORDEN PAYPAL ===")
        print(f"   Orden: {orden_compra.codigo_orden}")
        print(f"   Total: ${orden_compra.total}")
        
        # Obtener token de acceso
        token = PayPalService.get_access_token()
        if not token:
            print(f"   ❌ No se pudo obtener token de PayPal")
            return None
        
        print(f"   ✅ Token obtenido")
        
        url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'PayPal-Request-Id': str(uuid.uuid4()),
            'Prefer': 'return=representation'
        }
        
        # URLs dinámicas
        if request:
            base_url = request.build_absolute_uri('/').rstrip('/')
        else:
            base_url = settings.DOMAIN_URL
        
        return_url = f"{base_url}/cart/pago-exitoso/{orden_compra.codigo_orden}/"
        cancel_url = f"{base_url}/cart/pago-cancelado/{orden_compra.codigo_orden}/"
        
        print(f"   📍 Return URL: {return_url}")
        print(f"   📍 Cancel URL: {cancel_url}")
        
        # Preparar items para PayPal
        items = []
        for item in orden_compra.items.all():
            items.append({
                "name": item.producto.mazo.nombre[:127],
                "unit_amount": {
                    "currency_code": orden_compra.moneda,
                    "value": str(item.precio_unitario)
                },
                "quantity": str(item.cantidad),
                "description": f"{item.producto.mazo.set.nombre} - Producto Digital"[:127],
                "category": "DIGITAL_GOODS"
            })
        
        print(f"   📋 Items preparados: {len(items)}")
        
        # Payload para PayPal - CONFIGURACIÓN MÍNIMA Y SEGURA
        data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(orden_compra.codigo_orden),
                "amount": {
                    "currency_code": orden_compra.moneda,
                    "value": str(orden_compra.total),
                    "breakdown": {
                        "item_total": {
                            "currency_code": orden_compra.moneda,
                            "value": str(orden_compra.subtotal)
                        }
                    }
                },
                "items": items,
                "description": f"Tarotnaútica - Orden {orden_compra.codigo_orden}"
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Tarotnaútica",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING"
            }
        }
        
        try:
            print(f"   📤 Enviando orden a PayPal...")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data, 
                timeout=30
            )
            
            print(f"   📥 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                paypal_response = response.json()
                order_id = paypal_response.get('id')
                print(f"   🎉 ¡Orden creada exitosamente!")
                print(f"   📋 PayPal Order ID: {order_id}")
                return paypal_response
            else:
                print(f"   ❌ Error PayPal: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                logger.error(f"Error PayPal: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout creando orden PayPal")
            logger.error("Timeout creando orden PayPal")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   💥 Error de conexión: {e}")
            logger.error(f"Error de conexión creando orden PayPal: {e}")
            return None
        except Exception as e:
            print(f"   💥 Error inesperado: {e}")
            logger.error(f"Error inesperado creando orden PayPal: {e}")
            return None
        finally:
            print("=" * 35 + "\n")


# ============== VISTA PRINCIPAL CORREGIDA ============== #

@login_required
def crear_orden_paypal(request):
    """
    Crear orden PayPal - VERSIÓN CORREGIDA CON SERVICIO COMPLETO
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    
    try:
        print(f"\n🛒 === INICIANDO CREACIÓN DE ORDEN ===")
        print(f"Usuario: {request.user.email}")
        
        # Verificar configuración PayPal
        configuracion_ok = all([
            settings.PAYPAL_CLIENT_ID,
            settings.PAYPAL_CLIENT_SECRET,
            settings.PAYPAL_BASE_URL,
            settings.PAYPAL_MODE
        ])
        
        if not configuracion_ok:
            print(f"❌ Configuración PayPal incompleta")
            return JsonResponse({
                'success': False,
                'message': 'Configuración de pagos no disponible temporalmente'
            }, status=500)
        
        print(f"✅ Configuración PayPal verificada")
        
        # Obtener carrito del usuario
        carrito = get_object_or_404(Carrito, usuario=request.user)
        
        if not carrito.items.exists():
            print(f"❌ Carrito vacío")
            return JsonResponse({
                'success': False,
                'message': 'Tu carrito está vacío'
            }, status=400)
        
        print(f"🛍️ Carrito encontrado: {carrito.items.count()} items, total: ${carrito.total}")
        
        # Crear OrdenCompra
        orden = OrdenCompra.objects.create(
            usuario=request.user,
            codigo_orden=str(uuid.uuid4())[:8].upper(),
            subtotal=carrito.subtotal,
            total=carrito.total,
            moneda='USD',
            estado='creada'
        )
        
        print(f"📋 OrdenCompra creada: {orden.codigo_orden}")
        
        # Crear ItemOrden para cada producto
        items_creados = []
        for item_carrito in carrito.items.select_related('producto', 'producto__mazo'):
            item_orden = ItemOrden.objects.create(
                orden=orden,
                producto=item_carrito.producto,
                cantidad=item_carrito.cantidad,
                precio_unitario=item_carrito.precio_unitario
            )
            items_creados.append(item_orden)
        
        print(f"📦 Items de orden creados: {len(items_creados)}")
        
        # Crear orden en PayPal usando el servicio completo
        paypal_response = PayPalService.crear_orden_paypal(orden, request)
        
        if paypal_response and 'id' in paypal_response:
            # Actualizar orden con datos de PayPal
            orden.paypal_order_id = paypal_response['id']
            orden.estado = 'pendiente'
            orden.datos_paypal = paypal_response
            orden.save()
            
            print(f"🎉 ¡ÉXITO! Orden PayPal creada")
            print(f"   Order ID: {paypal_response['id']}")
            print(f"   Estado: {orden.estado}")
            
            return JsonResponse({
                'success': True,
                'order_id': paypal_response['id'],
                'message': 'Orden creada exitosamente',
                'debug_info': {
                    'orden_codigo': orden.codigo_orden,
                    'paypal_order_id': paypal_response['id'],
                    'total': str(orden.total),
                    'items_count': len(items_creados)
                }
            })
        else:
            print(f"💥 Error: No se pudo crear orden en PayPal")
            orden.estado = 'error'
            orden.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Error al procesar con PayPal. Por favor intenta nuevamente.'
            }, status=500)
            
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        logger.error(f"Error crítico en crear_orden_paypal: {e}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor. Intenta nuevamente.'
        }, status=500)
    finally:
        print("=" * 50 + "\n")


# ============== RESTO DE VISTAS (WEBHOOKS, ETC.) ============== #

@csrf_exempt
def webhook_paypal(request):
    """
    Webhook endpoint para recibir notificaciones de PayPal
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Obtener datos del webhook
        webhook_data = json.loads(request.body)
        event_type = webhook_data.get('event_type')
        resource = webhook_data.get('resource', {})
        
        print(f"📨 Webhook PayPal recibido: {event_type}")
        
        # Guardar log del webhook
        log = LogWebhookPayPal.objects.create(
            webhook_id=webhook_data.get('id', ''),
            event_type=event_type,
            resource_id=resource.get('id', ''),
            datos_completos=webhook_data
        )
        
        # Procesar según el tipo de evento
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            procesar_orden_aprobada(webhook_data, log)
        elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
            procesar_pago_completado(webhook_data, log)
        
        log.procesado = True
        log.save()
        
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error procesando webhook PayPal: {e}")
        return HttpResponse("Error", status=500)


def procesar_orden_aprobada(webhook_data, log):
    """
    Procesar orden aprobada por PayPal
    """
    try:
        resource = webhook_data.get('resource', {})
        order_id = resource.get('id')
        
        if order_id:
            orden = OrdenCompra.objects.filter(paypal_order_id=order_id).first()
            if orden:
                orden.estado = 'aprobada'
                orden.datos_paypal = resource
                orden.save()
                log.orden_relacionada = orden
                log.save()
                print(f"✅ Orden aprobada: {orden.codigo_orden}")
                
    except Exception as e:
        log.error_mensaje = str(e)
        log.save()
        logger.error(f"Error procesando orden aprobada: {e}")


def procesar_pago_completado(webhook_data, log):
    """
    Procesar pago completado en PayPal
    """
    try:
        resource = webhook_data.get('resource', {})
        order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
        payment_id = resource.get('id')
        
        if order_id:
            orden = OrdenCompra.objects.filter(paypal_order_id=order_id).first()
            if orden:
                orden.estado = 'pagada'
                orden.paypal_payment_id = payment_id
                orden.fecha_pago = timezone.now()
                orden.datos_paypal = resource
                orden.save()
                
                # Crear CompraProducto automáticamente
                compras_creadas = orden.crear_compras_productos()
                
                # Vaciar carrito del usuario
                orden.vaciar_carrito_usuario()
                
                log.orden_relacionada = orden
                log.save()
                
                print(f"✅ Pago completado: {orden.codigo_orden}")
                logger.info(f"Pago completado para orden {orden.codigo_orden}, {len(compras_creadas)} productos activados")
                
    except Exception as e:
        log.error_mensaje = str(e)
        log.save()
        logger.error(f"Error procesando pago completado: {e}")


@login_required
def pago_exitoso(request, codigo_orden):
    """
    Vista de confirmación de pago exitoso
    """
    orden = get_object_or_404(OrdenCompra, codigo_orden=codigo_orden, usuario=request.user)
    
    context = {
        'title': 'Pago Exitoso',
        'orden': orden,
    }
    
    return render(request, 'finanzas/pago_exitoso.html', context)


@login_required
def pago_cancelado(request, codigo_orden):
    """
    Vista cuando el usuario cancela el pago
    """
    orden = get_object_or_404(OrdenCompra, codigo_orden=codigo_orden, usuario=request.user)
    orden.estado = 'cancelada'
    orden.save()
    
    messages.warning(request, 'El pago fue cancelado. Los productos siguen en tu carrito.')
    return redirect('finanzas:ver_carrito')


# ============== DASHBOARD DE FINANZAS ============== #

@staff_member_required
def dashboard_finanzas(request):
    """
    Dashboard principal de finanzas
    """
    # Obtener fechas para filtros
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_año = hoy.replace(month=1, day=1)
    hace_30_dias = hoy - timedelta(days=30)
    
    # ============== MÉTRICAS PRINCIPALES ============== #
    
    # Ingresos por período
    ingresos_hoy = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date=hoy
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    ingresos_semana = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=inicio_semana
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    ingresos_mes = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=inicio_mes
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    ingresos_año = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=inicio_año
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Órdenes por estado
    ordenes_stats = OrdenCompra.objects.aggregate(
        total_ordenes=Count('id'),
        ordenes_pagadas=Count('id', filter=Q(estado='pagada')),
        ordenes_pendientes=Count('id', filter=Q(estado__in=['creada', 'pendiente', 'aprobada'])),
        ordenes_canceladas=Count('id', filter=Q(estado__in=['cancelada', 'error'])),
    )
    
    # Productos vendidos
    productos_vendidos_hoy = ItemOrden.objects.filter(
        orden__estado='pagada',
        orden__fecha_pago__date=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    productos_vendidos_mes = ItemOrden.objects.filter(
        orden__estado='pagada',
        orden__fecha_pago__date__gte=inicio_mes
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Ticket promedio
    ticket_promedio = OrdenCompra.objects.filter(
        estado='pagada'
    ).aggregate(promedio=Avg('total'))['promedio'] or Decimal('0')
    
    # Otras métricas básicas
    carritos_activos = Carrito.objects.filter(
        fecha_actualizacion__date__gte=hace_30_dias,
        items__isnull=False
    ).distinct().count()
    
    compras_completadas = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=hace_30_dias
    ).count()
    
    tasa_conversion = (compras_completadas / carritos_activos * 100) if carritos_activos > 0 else 0
    
    # Datos básicos para gráficos (simplificado)
    ventas_30_dias = []
    for i in range(30):
        fecha = hoy - timedelta(days=i)
        ingreso_dia = OrdenCompra.objects.filter(
            estado='pagada',
            fecha_pago__date=fecha
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        ventas_30_dias.append({
            'fecha': fecha.strftime('%d/%m'),
            'ingresos': float(ingreso_dia)
        })
    
    ventas_30_dias.reverse()
    
    # Ventas por mes (últimos 12 meses) - simplificado
    ventas_12_meses = []
    for i in range(12):
        fecha_mes = hoy.replace(day=1) - timedelta(days=32*i)
        inicio_mes_calc = fecha_mes.replace(day=1)
        
        ingreso_mes = OrdenCompra.objects.filter(
            estado='pagada',
            fecha_pago__date__gte=inicio_mes_calc,
            fecha_pago__date__lt=inicio_mes_calc.replace(month=inicio_mes_calc.month % 12 + 1) if inicio_mes_calc.month < 12 else inicio_mes_calc.replace(year=inicio_mes_calc.year + 1, month=1)
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        ventas_12_meses.append({
            'mes': calendar.month_name[inicio_mes_calc.month][:3],
            'año': inicio_mes_calc.year,
            'ingresos': float(ingreso_mes)
        })
    
    ventas_12_meses.reverse()
    
    # Context simplificado
    context = {
        'title': 'Dashboard de Finanzas',
        'ingresos': {
            'hoy': ingresos_hoy,
            'semana': ingresos_semana,
            'mes': ingresos_mes,
            'año': ingresos_año,
        },
        'ordenes': ordenes_stats,
        'productos_vendidos': {
            'hoy': productos_vendidos_hoy,
            'mes': productos_vendidos_mes,
        },
        'ticket_promedio': ticket_promedio,
        'tasa_conversion': round(tasa_conversion, 2),
        'ventas_30_dias': ventas_30_dias,
        'ventas_12_meses': ventas_12_meses,
        'carritos_activos': carritos_activos,
        'compras_completadas': compras_completadas,
        'fecha_actual': timezone.now(),
        'top_productos': [],  # Simplificado por ahora
        'top_usuarios': [],   # Simplificado por ahora
        'metodos_pago': [],   # Simplificado por ahora
    }
    
    return render(request, 'finanzas/dashboard.html', context)

# Otras vistas simplificadas
@staff_member_required
def reportes_detallados(request):
    """
    Página de reportes detallados con filtros avanzados
    """
    # Obtener parámetros de filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado_filtro = request.GET.get('estado', 'pagada')
    
    # Fechas por defecto (último mes)
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30)).isoformat()
    if not fecha_fin:
        fecha_fin = timezone.now().date().isoformat()
    
    # Query base
    ordenes = OrdenCompra.objects.select_related('usuario').prefetch_related('items__producto__mazo')
    
    # Aplicar filtros
    if estado_filtro:
        ordenes = ordenes.filter(estado=estado_filtro)
    if fecha_inicio:
        ordenes = ordenes.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        ordenes = ordenes.filter(fecha_creacion__date__lte=fecha_fin)
    
    # Estadísticas del período filtrado
    stats_periodo = ordenes.aggregate(
        total_ingresos=Sum('total'),
        total_ordenes=Count('id'),
        ticket_promedio=Avg('total'),
        total_productos=Sum('items__cantidad')
    )
    
    # Ordenes paginadas
    from django.core.paginator import Paginator
    paginator = Paginator(ordenes.order_by('-fecha_creacion'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Reportes Detallados',
        'page_obj': page_obj,
        'stats_periodo': stats_periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado_filtro,
        'estados_opciones': OrdenCompra.ESTADO_CHOICES,
    }
    
    return render(request, 'finanzas/reportes.html', context)

@staff_member_required
def exportar_ventas_csv(request):
    """
    Exportar ventas a CSV
    """
    import csv
    
    # Obtener parámetros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Query de órdenes
    ordenes = OrdenCompra.objects.filter(estado='pagada')
    
    if fecha_inicio:
        ordenes = ordenes.filter(fecha_pago__date__gte=fecha_inicio)
    if fecha_fin:
        ordenes = ordenes.filter(fecha_pago__date__lte=fecha_fin)
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ventas_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Headers
    writer.writerow([
        'Fecha', 'Orden', 'Usuario', 'Email', 'Producto', 'Cantidad', 
        'Precio Unitario', 'Subtotal', 'Total Orden', 'PayPal ID'
    ])
    
    # Datos
    for orden in ordenes.prefetch_related('items__producto__mazo'):
        for item in orden.items.all():
            writer.writerow([
                orden.fecha_pago.strftime('%d/%m/%Y') if orden.fecha_pago else '',
                orden.codigo_orden,
                orden.usuario.nombre,
                orden.usuario.email,
                item.producto.mazo.nombre,
                item.cantidad,
                item.precio_unitario,
                item.subtotal,
                orden.total,
                orden.paypal_payment_id or ''
            ])
    
    return response

@staff_member_required  
def api_metricas_tiempo_real(request):
    """
    API para métricas en tiempo real (AJAX)
    """
    hoy = timezone.now().date()
    
    # Métricas del día
    ingresos_hoy = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date=hoy
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    ordenes_hoy = OrdenCompra.objects.filter(
        fecha_creacion__date=hoy
    ).count()
    
    productos_vendidos_hoy = ItemOrden.objects.filter(
        orden__estado='pagada',
        orden__fecha_pago__date=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Carritos activos (última hora)
    hace_una_hora = timezone.now() - timedelta(hours=1)
    carritos_activos_hora = Carrito.objects.filter(
        fecha_actualizacion__gte=hace_una_hora,
        items__isnull=False
    ).distinct().count()
    
# Endpoint para probar conexión desde debug
@staff_member_required
def test_paypal_connection(request):
    """
    Endpoint AJAX para probar conexión PayPal desde la vista de debug
    """
    if not settings.DEBUG:
        return JsonResponse({'success': False, 'error': 'Only available in DEBUG mode'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        # Usar el servicio PayPal para obtener token
        token = PayPalService.get_access_token()
        
        if token:
            return JsonResponse({
                'success': True,
                'message': 'Conexión PayPal exitosa',
                'token_preview': token[:20] + '...' if len(token) > 20 else token,
                'token_length': len(token)
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'No se pudo obtener token de PayPal'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })

# Imports para las utilidades
from .utils import verificar_configuracion_paypal, get_paypal_config_status

@staff_member_required
def debug_paypal(request):
    """
    Vista de debug para verificar configuración PayPal
    Solo accesible para staff en modo DEBUG
    """
    from django.http import Http404
    
    if not settings.DEBUG:
        raise Http404("Vista no disponible en producción")
    
    # Ejecutar verificación completa
    configuracion_ok = verificar_configuracion_paypal()
    
    # Obtener estado de configuración
    config_status = get_paypal_config_status()
    
    # Información adicional
    debug_info = {
        'configuracion_completa': configuracion_ok,
        'config_status': config_status,
        'settings_info': {
            'PAYPAL_MODE': getattr(settings, 'PAYPAL_MODE', 'NOT SET'),
            'PAYPAL_BASE_URL': getattr(settings, 'PAYPAL_BASE_URL', 'NOT SET'),
            'DOMAIN_URL': getattr(settings, 'DOMAIN_URL', 'NOT SET'),
            'PAYPAL_CLIENT_ID_LENGTH': len(settings.PAYPAL_CLIENT_ID) if settings.PAYPAL_CLIENT_ID else 0,
            'PAYPAL_CLIENT_SECRET_LENGTH': len(settings.PAYPAL_CLIENT_SECRET) if settings.PAYPAL_CLIENT_SECRET else 0,
        },
        'urls_info': {
            'current_domain': request.build_absolute_uri('/').rstrip('/'),
            'expected_return_url': request.build_absolute_uri('/cart/pago-exitoso/TEST123/'),
            'expected_cancel_url': request.build_absolute_uri('/cart/pago-cancelado/TEST123/'),
        }
    }
    
    context = {
        'title': 'Debug PayPal Configuration',
        'debug_info': debug_info,
    }
    
    return render(request, 'finanzas/debug_paypal.html', context)