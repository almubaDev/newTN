from django.contrib import admin
from .models import TarotProduct

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