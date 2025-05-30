# finanzas/views.py - VISTA COMPLETA CORREGIDA
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


# ============== NUEVAS VISTAS PAYPAL ============== #

class PayPalService:
    """
    Servicio para manejar operaciones con PayPal
    """
    
    @staticmethod
    def get_access_token():
        """
        Obtener token de acceso de PayPal
        """
        url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
        
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        }
        
        data = 'grant_type=client_credentials'
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
            )
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            logger.error(f"Error obteniendo token PayPal: {e}")
            return None
    
    @staticmethod
    def crear_orden_paypal(orden_compra):
        """
        Crear orden en PayPal
        """
        token = PayPalService.get_access_token()
        if not token:
            return None
        
        url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        
        # Crear items para PayPal
        items = []
        for item in orden_compra.items.all():
            items.append({
                "name": item.producto.mazo.nombre,
                "unit_amount": {
                    "currency_code": orden_compra.moneda,
                    "value": str(item.precio_unitario)
                },
                "quantity": str(item.cantidad),
                "description": f"{item.producto.mazo.set.nombre} - {item.producto.get_total_cartas} cartas",
                "category": "DIGITAL_GOODS"
            })
        
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
                "description": f"Compra en Tarotnaútica - Orden {orden_compra.codigo_orden}"
            }],
            "application_context": {
                "return_url": f"https://tarotnautica.store/cart/pago-exitoso/{orden_compra.codigo_orden}/",
                "cancel_url": f"https://tarotnautica.store/cart/pago-cancelado/{orden_compra.codigo_orden}/",
                "brand_name": "Tarotnaútica",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creando orden PayPal: {e}")
            return None


@login_required
def crear_orden_paypal(request):
    """
    Crear orden PayPal desde el carrito
    """
    try:
        carrito = get_object_or_404(Carrito, usuario=request.user)
        
        if not carrito.items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Tu carrito está vacío'
            })
        
        # Crear OrdenCompra
        orden = OrdenCompra.objects.create(
            usuario=request.user,
            codigo_orden=str(uuid.uuid4())[:8].upper(),
            subtotal=carrito.subtotal,
            total=carrito.total,
            moneda='USD',
            estado='creada'
        )
        
        # Crear ItemOrden desde el carrito
        for item_carrito in carrito.items.all():
            ItemOrden.objects.create(
                orden=orden,
                producto=item_carrito.producto,
                cantidad=item_carrito.cantidad,
                precio_unitario=item_carrito.precio_unitario
            )
        
        # Crear orden en PayPal
        paypal_response = PayPalService.crear_orden_paypal(orden)
        
        if paypal_response and 'id' in paypal_response:
            # Guardar ID de PayPal
            orden.paypal_order_id = paypal_response['id']
            orden.estado = 'pendiente'
            orden.save()
            
            # Buscar link de aprobación
            approve_url = None
            for link in paypal_response.get('links', []):
                if link.get('rel') == 'approve':
                    approve_url = link.get('href')
                    break
            
            return JsonResponse({
                'success': True,
                'order_id': paypal_response['id'],
                'approve_url': approve_url
            })
        else:
            orden.estado = 'error'
            orden.save()
            return JsonResponse({
                'success': False,
                'message': 'Error al crear orden en PayPal'
            })
            
    except Exception as e:
        logger.error(f"Error creando orden PayPal: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno: {str(e)}'
        })


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



# ============== DASHBOARD DE FINANZAS - CORREGIDO ============== #

@staff_member_required
def dashboard_finanzas(request):
    """
    Dashboard principal de finanzas - CORREGIDO COMPLETAMENTE
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
    
    # ============== GRÁFICOS ============== #
    
    # Ventas últimos 30 días
    ventas_30_dias = []
    for i in range(30):
        fecha = hoy - timedelta(days=i)
        ingreso_dia = OrdenCompra.objects.filter(
            estado='pagada',
            fecha_pago__date=fecha
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        ventas_30_dias.append({
            'fecha': fecha.strftime('%d/%m'),
            'ingresos': float(ingreso_dia),
            'fecha_completa': fecha.isoformat()
        })
    
    ventas_30_dias.reverse()  # Mostrar del más antiguo al más reciente
    
    # Ventas por mes (últimos 12 meses)
    ventas_12_meses = []
    for i in range(12):
        fecha_mes = hoy.replace(day=1) - timedelta(days=32*i)
        inicio_mes_calc = fecha_mes.replace(day=1)
        fin_mes = (inicio_mes_calc.replace(month=inicio_mes_calc.month % 12 + 1, day=1) - timedelta(days=1)) if inicio_mes_calc.month < 12 else inicio_mes_calc.replace(year=inicio_mes_calc.year + 1, month=1, day=1) - timedelta(days=1)
        
        ingreso_mes = OrdenCompra.objects.filter(
            estado='pagada',
            fecha_pago__date__gte=inicio_mes_calc,
            fecha_pago__date__lte=fin_mes
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        ventas_12_meses.append({
            'mes': calendar.month_name[inicio_mes_calc.month][:3],
            'año': inicio_mes_calc.year,
            'ingresos': float(ingreso_mes)
        })
    
    ventas_12_meses.reverse()
    
    # ============== TOP PRODUCTOS - CORREGIDO ============== #
    
    top_productos = ItemOrden.objects.filter(
        orden__estado='pagada',
        orden__fecha_pago__date__gte=hace_30_dias
    ).values(
        'producto__mazo__nombre',
        'producto__mazo__set__nombre',
        'producto__id'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        # CALCULAR subtotal usando F() y operaciones matemáticas
        ingresos_generados=Sum(F('cantidad') * F('precio_unitario')),
        ordenes_count=Count('orden', distinct=True)
    ).order_by('-cantidad_vendida')[:10]
    
    # ============== USUARIOS TOP - CORREGIDO ============== #
    
    top_usuarios = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=hace_30_dias
    ).values(
        'usuario__email',
        'usuario__nombre'
    ).annotate(
        total_gastado=Sum('total'),
        ordenes_count=Count('id'),
        productos_count=Sum('items__cantidad')
    ).order_by('-total_gastado')[:10]
    
    # ============== CONVERSIÓN ============== #
    
    # Carritos vs Compras (últimos 30 días)
    carritos_activos = Carrito.objects.filter(
        fecha_actualizacion__date__gte=hace_30_dias,
        items__isnull=False
    ).distinct().count()
    
    compras_completadas = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=hace_30_dias
    ).count()
    
    tasa_conversion = (compras_completadas / carritos_activos * 100) if carritos_activos > 0 else 0
    
    # ============== MÉTODOS DE PAGO - CORREGIDO ============== #
    
    metodos_pago = OrdenCompra.objects.filter(
        estado='pagada',
        fecha_pago__date__gte=hace_30_dias
    ).aggregate(
        paypal_count=Count('id', filter=Q(paypal_payment_id__isnull=False)),
        paypal_ingresos=Sum('total', filter=Q(paypal_payment_id__isnull=False)),
        otro_count=Count('id', filter=Q(paypal_payment_id__isnull=True)),
        otro_ingresos=Sum('total', filter=Q(paypal_payment_id__isnull=True))
    )
    
    # Formatear métodos de pago para el template
    metodos_pago_formateados = []
    if metodos_pago['paypal_count']:
        metodos_pago_formateados.append({
            'metodo': 'PayPal',
            'count': metodos_pago['paypal_count'],
            'ingresos': metodos_pago['paypal_ingresos'] or Decimal('0')
        })
    if metodos_pago['otro_count']:
        metodos_pago_formateados.append({
            'metodo': 'Otro',
            'count': metodos_pago['otro_count'],
            'ingresos': metodos_pago['otro_ingresos'] or Decimal('0')
        })
    
    # ============== CONTEXTO ============== #
    
    context = {
        'title': 'Dashboard de Finanzas',
        
        # Métricas principales
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
        
        # Datos para gráficos
        'ventas_30_dias': ventas_30_dias,
        'ventas_12_meses': ventas_12_meses,
        
        # Top lists
        'top_productos': top_productos,
        'top_usuarios': top_usuarios,
        'metodos_pago': metodos_pago_formateados,
        
        # Contadores adicionales
        'carritos_activos': carritos_activos,
        'compras_completadas': compras_completadas,
        
        # Fechas para referencia
        'fecha_actual': timezone.now(),  # datetime completo en lugar de .date()
        'periodo_analisis': '30 días',
    }
    
    return render(request, 'finanzas/dashboard.html', context)


@staff_member_required
def reportes_detallados(request):
    """
    Página de reportes detallados con filtros avanzados
    """
    # Obtener parámetros de filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado_filtro = request.GET.get('estado', 'pagada')
    producto_filtro = request.GET.get('producto')
    usuario_filtro = request.GET.get('usuario')
    
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
    
    if producto_filtro:
        ordenes = ordenes.filter(items__producto_id=producto_filtro)
    
    if usuario_filtro:
        ordenes = ordenes.filter(usuario_id=usuario_filtro)
    
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
    
    # Listas para filtros
    productos_disponibles = TarotProduct.objects.select_related('mazo').all()
    from user.models import CustomUser
    usuarios_con_compras = CustomUser.objects.filter(ordenes_compra__isnull=False).distinct()
    
    context = {
        'title': 'Reportes Detallados',
        'page_obj': page_obj,
        'stats_periodo': stats_periodo,
        
        # Filtros actuales
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado_filtro,
        'producto_filtro': producto_filtro,
        'usuario_filtro': usuario_filtro,
        
        # Opciones para filtros
        'estados_opciones': OrdenCompra.ESTADO_CHOICES,
        'productos_disponibles': productos_disponibles,
        'usuarios_con_compras': usuarios_con_compras,
    }
    
    return render(request, 'finanzas/reportes.html', context)


@staff_member_required
def exportar_ventas_csv(request):
    """
    Exportar ventas a CSV
    """
    import csv
    from django.http import HttpResponse
    
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
    
    return JsonResponse({
        'ingresos_hoy': float(ingresos_hoy),
        'ordenes_hoy': ordenes_hoy,
        'productos_vendidos_hoy': productos_vendidos_hoy,
        'carritos_activos_hora': carritos_activos_hora,
        'timestamp': timezone.now().isoformat()
    })