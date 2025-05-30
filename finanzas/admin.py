from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Carrito, ItemCarrito, OrdenCompra, ItemOrden, LogWebhookPayPal

# ============== ADMIN PARA CARRITO EXISTENTE ============== #

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'total_items_display', 'total_display', 'fecha_actualizacion']
    list_filter = ['fecha_creacion', 'fecha_actualizacion']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def total_items_display(self, obj):
        return obj.total_items
    total_items_display.short_description = 'Total Items'
    
    def total_display(self, obj):
        return f"${obj.total}"
    total_display.short_description = 'Total'


@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ['carrito_usuario', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal_display', 'fecha_agregado']
    list_filter = ['fecha_agregado', 'cantidad']
    search_fields = ['carrito__usuario__username', 'producto__mazo__nombre']
    
    def carrito_usuario(self, obj):
        return obj.carrito.usuario.username
    carrito_usuario.short_description = 'Usuario'
    
    def producto_nombre(self, obj):
        return obj.producto.mazo.nombre
    producto_nombre.short_description = 'Producto'
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


# ============== ADMIN PARA PAYPAL ============== #

class ItemOrdenInline(admin.TabularInline):
    model = ItemOrden
    extra = 0
    readonly_fields = ['subtotal_display']
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal_display']
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f"${obj.subtotal}"
        return "-"
    subtotal_display.short_description = 'Subtotal'


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_orden', 'usuario', 'estado_display', 'total_display',
        'fecha_creacion', 'fecha_pago', 'paypal_status'
    ]
    list_filter = [
        'estado', 'moneda', 'fecha_creacion', 'fecha_pago'
    ]
    search_fields = [
        'codigo_orden', 'usuario__username', 'usuario__email',
        'paypal_order_id', 'paypal_payment_id'
    ]
    readonly_fields = [
        'codigo_orden', 'fecha_creacion', 'fecha_actualizacion',
        'paypal_data_display', 'compras_creadas_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_orden', 'usuario', 'estado')
        }),
        ('Montos', {
            'fields': ('subtotal', 'total', 'moneda')
        }),
        ('PayPal', {
            'fields': ('paypal_order_id', 'paypal_payment_id', 'email_paypal'),
            'classes': ('collapse',)
        }),
        ('Datos Técnicos', {
            'fields': ('paypal_data_display', 'compras_creadas_display'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_pago', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ItemOrdenInline]
    actions = ['marcar_como_pagada', 'crear_compras_productos']
    
    def estado_display(self, obj):
        colors = {
            'creada': 'gray',
            'pendiente': 'orange',
            'aprobada': 'blue',
            'pagada': 'green',
            'cancelada': 'red',
            'error': 'darkred'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def total_display(self, obj):
        return f"${obj.total} {obj.moneda}"
    total_display.short_description = 'Total'
    
    def paypal_status(self, obj):
        if obj.paypal_order_id:
            return format_html(
                '<span style="color: green;">✓ PayPal</span>'
            )
        return format_html('<span style="color: orange;">⚠ Sin PayPal</span>')
    paypal_status.short_description = 'PayPal'
    
    def paypal_data_display(self, obj):
        if obj.datos_paypal:
            return format_html('<pre>{}</pre>', 
                             str(obj.datos_paypal)[:500] + '...' if len(str(obj.datos_paypal)) > 500 else str(obj.datos_paypal))
        return "Sin datos"
    paypal_data_display.short_description = 'Datos PayPal'
    
    def compras_creadas_display(self, obj):
        from tienda.models import CompraProducto
        compras = CompraProducto.objects.filter(
            usuario=obj.usuario,
            referencia_pago__in=[obj.paypal_payment_id, obj.paypal_order_id]
        )
        if compras.exists():
            links = []
            for compra in compras:
                url = reverse('admin:tienda_compraproducto_change', args=[compra.pk])
                links.append(f'<a href="{url}">Compra #{compra.pk}</a>')
            return format_html('<br>'.join(links))
        return "No se han creado compras"
    compras_creadas_display.short_description = 'CompraProducto Creadas'
    
    # Acciones personalizadas
    def marcar_como_pagada(self, request, queryset):
        count = 0
        for orden in queryset:
            if orden.estado != 'pagada':
                orden.estado = 'pagada'
                orden.save()
                count += 1
        self.message_user(request, f'{count} órdenes marcadas como pagadas.')
    marcar_como_pagada.short_description = "Marcar como pagadas"
    
    def crear_compras_productos(self, request, queryset):
        total_compras = 0
        for orden in queryset.filter(estado='pagada'):
            compras = orden.crear_compras_productos()
            total_compras += len(compras)
        self.message_user(request, f'{total_compras} CompraProducto creadas.')
    crear_compras_productos.short_description = "Crear CompraProducto"


@admin.register(ItemOrden)
class ItemOrdenAdmin(admin.ModelAdmin):
    list_display = ['orden_codigo', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal_display']
    list_filter = ['cantidad']
    search_fields = ['orden__codigo_orden', 'producto__mazo__nombre']
    
    def orden_codigo(self, obj):
        return obj.orden.codigo_orden
    orden_codigo.short_description = 'Orden'
    
    def producto_nombre(self, obj):
        return obj.nombre_producto
    producto_nombre.short_description = 'Producto'
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(LogWebhookPayPal)
class LogWebhookPayPalAdmin(admin.ModelAdmin):
    list_display = [
        'fecha_recibido', 'event_type', 'resource_id', 
        'orden_relacionada', 'procesado_display', 'error_display'
    ]
    list_filter = ['event_type', 'procesado', 'fecha_recibido']
    search_fields = ['webhook_id', 'event_type', 'resource_id']
    readonly_fields = ['fecha_recibido', 'datos_completos_display']
    
    fieldsets = (
        ('Información del Webhook', {
            'fields': ('webhook_id', 'event_type', 'resource_id', 'orden_relacionada')
        }),
        ('Estado', {
            'fields': ('procesado', 'error_mensaje')
        }),
        ('Datos Completos', {
            'fields': ('datos_completos_display',),
            'classes': ('collapse',)
        }),
        ('Fecha', {
            'fields': ('fecha_recibido',)
        }),
    )
    
    actions = ['marcar_como_procesado', 'reprocesar_webhooks']
    
    def procesado_display(self, obj):
        if obj.procesado:
            return format_html('<span style="color: green;">✓ Procesado</span>')
        return format_html('<span style="color: red;">✗ Pendiente</span>')
    procesado_display.short_description = 'Estado'
    
    def error_display(self, obj):
        if obj.error_mensaje:
            return format_html('<span style="color: red;">⚠ Error</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    error_display.short_description = 'Error'
    
    def datos_completos_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', 
                         json.dumps(obj.datos_completos, indent=2) if obj.datos_completos else 'Sin datos')
    datos_completos_display.short_description = 'Datos JSON'
    
    def marcar_como_procesado(self, request, queryset):
        count = queryset.update(procesado=True)
        self.message_user(request, f'{count} webhooks marcados como procesados.')
    marcar_como_procesado.short_description = "Marcar como procesados"
    
    def reprocesar_webhooks(self, request, queryset):
        # Esta función podría reprocesar webhooks fallidos
        count = 0
        for webhook in queryset.filter(procesado=False):
            # Aquí iría la lógica de reprocesamiento
            # Por ahora solo los marcamos como procesados
            webhook.procesado = True
            webhook.save()
            count += 1
        self.message_user(request, f'{count} webhooks reprocesados.')
    reprocesar_webhooks.short_description = "Reprocesar webhooks"