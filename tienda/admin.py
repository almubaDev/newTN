from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import TarotProduct, CompraProducto


@admin.register(TarotProduct)
class TarotProductAdmin(admin.ModelAdmin):
    """
    Configuración del admin para productos de tarot
    """
    list_display = [
        'mazo', 'precio', 'precio_oferta', 'estado', 
        'destacado', 'orden', 'fecha_creacion'
    ]
    list_filter = ['estado', 'destacado', 'mazo__set', 'fecha_creacion']
    search_fields = ['mazo__nombre', 'mazo__codigo', 'descripcion_adicional']
    list_editable = ['precio', 'precio_oferta', 'estado', 'destacado', 'orden']
    ordering = ['orden', '-destacado', '-fecha_creacion']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('mazo', 'estado', 'destacado', 'orden')
        }),
        ('Precios', {
            'fields': ('precio', 'precio_oferta')
        }),
        ('Compra', {
            'fields': ('link_compra',)
        }),
        ('Descripción Adicional', {
            'fields': ('descripcion_adicional',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mazo', 'mazo__set')
    
    # Acciones personalizadas
    actions = ['activar_productos', 'desactivar_productos', 'marcar_destacados']
    
    def activar_productos(self, request, queryset):
        queryset.update(estado='activo')
        self.message_user(request, f'Se activaron {queryset.count()} productos.')
    activar_productos.short_description = "Activar productos seleccionados"
    
    def desactivar_productos(self, request, queryset):
        queryset.update(estado='inactivo')
        self.message_user(request, f'Se desactivaron {queryset.count()} productos.')
    desactivar_productos.short_description = "Desactivar productos seleccionados"
    
    def marcar_destacados(self, request, queryset):
        queryset.update(destacado=True)
        self.message_user(request, f'Se marcaron {queryset.count()} productos como destacados.')
    marcar_destacados.short_description = "Marcar como destacados"


@admin.register(CompraProducto)
class CompraProductoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para compras de productos
    """
    list_display = [
        'usuario', 'producto_nombre', 'precio_pagado', 
        'metodo_pago', 'estado', 'fecha_compra'
    ]
    list_filter = [
        'estado', 'metodo_pago', 'fecha_compra', 
        'producto__mazo__set', 'producto__destacado'
    ]
    search_fields = [
        'usuario__email', 'usuario__nombre', 'usuario__apellido',
        'producto__mazo__nombre', 'referencia_pago'
    ]
    list_editable = ['estado', 'precio_pagado']
    readonly_fields = ['fecha_compra', 'fecha_actualizacion']
    ordering = ['-fecha_compra']
    list_per_page = 25
    
    fieldsets = (
        ('Información de la Compra', {
            'fields': ('usuario', 'producto', 'estado')
        }),
        ('Detalles del Pago', {
            'fields': ('precio_pagado', 'metodo_pago', 'referencia_pago')
        }),
        ('Notas y Administración', {
            'fields': ('notas_admin',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_compra', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'usuario', 'producto', 'producto__mazo', 'producto__mazo__set'
        )
    
    def producto_nombre(self, obj):
        """Muestra el nombre del producto"""
        return obj.nombre_producto
    producto_nombre.short_description = 'Producto'
    producto_nombre.admin_order_field = 'producto__mazo__nombre'
    
    # Acciones personalizadas
    actions = ['marcar_completadas', 'marcar_pendientes', 'marcar_canceladas']
    
    def marcar_completadas(self, request, queryset):
        """Marca compras como completadas"""
        count = queryset.update(estado='completada')
        self.message_user(request, f'Se marcaron {count} compra{"s" if count != 1 else ""} como completadas.')
    marcar_completadas.short_description = "Marcar como completadas"
    
    def marcar_pendientes(self, request, queryset):
        """Marca compras como pendientes"""
        count = queryset.update(estado='pendiente')
        self.message_user(request, f'Se marcaron {count} compra{"s" if count != 1 else ""} como pendientes.')
    marcar_pendientes.short_description = "Marcar como pendientes"
    
    def marcar_canceladas(self, request, queryset):
        """Marca compras como canceladas"""
        count = queryset.update(estado='cancelada')
        self.message_user(request, f'Se marcaron {count} compra{"s" if count != 1 else ""} como canceladas.')
    marcar_canceladas.short_description = "Marcar como canceladas"