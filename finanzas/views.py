# 3. finanzas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import F
from .models import Carrito, ItemCarrito
from tienda.models import TarotProduct
import json

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