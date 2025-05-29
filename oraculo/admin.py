from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Set, Mazo, Carta


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Sets de cartas
    """
    list_display = [
        'nombre', 'codigo', 'total_mazos', 'total_cartas_set', 
        'fecha_creacion', 'fecha_actualizacion'
    ]
    list_filter = ['fecha_creacion', 'fecha_actualizacion']
    search_fields = ['nombre', 'codigo', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def total_mazos(self, obj):
        """Muestra el total de mazos en el set"""
        count = obj.mazos.count()
        if count > 0:
            url = reverse('admin:oraculo_mazo_changelist') + f'?set__id__exact={obj.id}'
            return format_html('<a href="{}">{} mazo{}</a>', 
                             url, count, 's' if count != 1 else '')
        return '0 mazos'
    total_mazos.short_description = 'Mazos'
    
    def total_cartas_set(self, obj):
        """Muestra el total de cartas en todos los mazos del set"""
        total = sum(mazo.total_cartas() for mazo in obj.mazos.all())
        if total > 0:
            return f'{total} carta{"s" if total != 1 else ""}'
        return '0 cartas'
    total_cartas_set.short_description = 'Total Cartas'
    
    # Acciones personalizadas
    actions = ['duplicar_sets']
    
    def duplicar_sets(self, request, queryset):
        """Acción para duplicar sets seleccionados"""
        for set_obj in queryset:
            # Crear copia del set con nombre modificado
            nuevo_codigo = f"{set_obj.codigo}_COPY"
            nuevo_nombre = f"{set_obj.nombre} (Copia)"
            
            Set.objects.create(
                nombre=nuevo_nombre,
                codigo=nuevo_codigo,
                descripcion=f"Copia de: {set_obj.descripcion}"
            )
        
        count = queryset.count()
        self.message_user(request, f'Se duplicaron {count} set{"s" if count != 1 else ""}.')
    duplicar_sets.short_description = "Duplicar sets seleccionados"


@admin.register(Mazo)
class MazoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Mazos de cartas
    """
    list_display = [
        'imagen_thumbnail', 'nombre', 'codigo', 'set', 'total_cartas_mazo', 
        'tiene_producto', 'fecha_creacion'
    ]
    list_filter = ['set', 'fecha_creacion', 'fecha_actualizacion']
    search_fields = ['nombre', 'codigo', 'descripcion', 'set__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'imagen_preview']
    ordering = ['set__nombre', 'nombre']
    list_per_page = 20
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'set')
        }),
        ('Contenido', {
            'fields': ('descripcion',)
        }),
        ('Imagen', {
            'fields': ('imagen_reverso', 'imagen_preview')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def imagen_thumbnail(self, obj):
        """Miniatura de la imagen del reverso"""
        if obj.imagen_reverso:
            return format_html(
                '<img src="{}" width="30" height="40" style="object-fit: cover; border-radius: 4px;" />',
                obj.imagen_reverso.url
            )
        return '📄'
    imagen_thumbnail.short_description = 'Imagen'
    
    def imagen_preview(self, obj):
        """Preview más grande de la imagen"""
        if obj.imagen_reverso:
            return format_html(
                '<img src="{}" width="150" height="200" style="object-fit: cover; border-radius: 8px; border: 2px solid #ddd;" />',
                obj.imagen_reverso.url
            )
        return 'Sin imagen'
    imagen_preview.short_description = 'Vista Previa'
    
    def total_cartas_mazo(self, obj):
        """Muestra el total de cartas en el mazo con enlace"""
        count = obj.total_cartas()
        if count > 0:
            url = reverse('admin:oraculo_carta_changelist') + f'?mazo__id__exact={obj.id}'
            return format_html('<a href="{}">{} carta{}</a>', 
                             url, count, 's' if count != 1 else '')
        return '0 cartas'
    total_cartas_mazo.short_description = 'Cartas'
    
    def tiene_producto(self, obj):
        """Indica si el mazo tiene un producto asociado en la tienda"""
        try:
            if hasattr(obj, 'producto'):
                producto = obj.producto
                url = reverse('admin:tienda_tarotproduct_change', args=[producto.id])
                estado_color = {
                    'activo': '#28a745',
                    'inactivo': '#6c757d', 
                    'agotado': '#dc3545',
                    'proximamente': '#ffc107'
                }.get(producto.estado, '#6c757d')
                
                return format_html(
                    '<a href="{}" style="color: {}; font-weight: bold;">✓ {}</a>',
                    url, estado_color, producto.get_estado_display()
                )
        except:
            pass
        return format_html('<span style="color: #dc3545;">✗ Sin producto</span>')
    tiene_producto.short_description = 'Producto Tienda'
    
    # Acciones personalizadas
    actions = ['crear_productos_tienda', 'duplicar_mazos']
    
    def crear_productos_tienda(self, request, queryset):
        """Crear productos de tienda para mazos que no los tienen"""
        try:
            from tienda.models import TarotProduct
            creados = 0
            
            for mazo in queryset:
                if not hasattr(mazo, 'producto'):
                    TarotProduct.objects.create(
                        mazo=mazo,
                        precio=25.00,  # Precio por defecto
                        link_compra='https://ejemplo.com/comprar',
                        estado='inactivo'  # Crear inactivo para que se configure después
                    )
                    creados += 1
            
            if creados > 0:
                self.message_user(request, f'Se crearon {creados} producto{"s" if creados != 1 else ""} de tienda.')
            else:
                self.message_user(request, 'Todos los mazos seleccionados ya tienen productos.', level='WARNING')
        except ImportError:
            self.message_user(request, 'No se pudo importar el modelo TarotProduct de la tienda.', level='ERROR')
    crear_productos_tienda.short_description = "Crear productos de tienda"
    
    def duplicar_mazos(self, request, queryset):
        """Duplicar mazos seleccionados"""
        for mazo in queryset:
            nuevo_codigo = f"{mazo.codigo}_COPY"
            nuevo_nombre = f"{mazo.nombre} (Copia)"
            
            Mazo.objects.create(
                nombre=nuevo_nombre,
                codigo=nuevo_codigo,
                descripcion=f"Copia de: {mazo.descripcion}",
                imagen_reverso=mazo.imagen_reverso,
                set=mazo.set
            )
        
        count = queryset.count()
        self.message_user(request, f'Se duplicaron {count} mazo{"s" if count != 1 else ""}.')
    duplicar_mazos.short_description = "Duplicar mazos seleccionados"


@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Cartas individuales
    """
    list_display = [
        'imagen_thumbnail', 'numero', 'nombre', 'mazo', 'set_nombre', 
        'tiene_significado_invertido', 'fecha_creacion'
    ]
    list_filter = [
        'mazo__set', 'mazo', 'fecha_creacion', 
        ('significado_invertido', admin.EmptyFieldListFilter)
    ]
    search_fields = [
        'nombre', 'numero', 'mazo__nombre', 'mazo__set__nombre',
        'significado_normal', 'significado_invertido'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'imagen_preview']
    ordering = ['mazo__set__nombre', 'mazo__nombre', 'numero']
    list_per_page = 25
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero', 'nombre', 'mazo')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Significados', {
            'fields': ('significado_normal', 'significado_invertido'),
            'description': 'El significado invertido es opcional para oráculos que no manejan posiciones invertidas.'
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def imagen_thumbnail(self, obj):
        """Miniatura de la imagen de la carta"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="25" height="35" style="object-fit: cover; border-radius: 4px;" />',
                obj.imagen.url
            )
        return '🃏'
    imagen_thumbnail.short_description = 'Img'
    
    def imagen_preview(self, obj):
        """Preview de la imagen de la carta"""
        if obj.imagen:
            return format_html(
                '<img src="{}" width="120" height="160" style="object-fit: cover; border-radius: 8px; border: 2px solid #ddd;" />',
                obj.imagen.url
            )
        return 'Sin imagen'
    imagen_preview.short_description = 'Vista Previa'
    
    def set_nombre(self, obj):
        """Nombre del set al que pertenece"""
        return obj.mazo.set.nombre
    set_nombre.short_description = 'Set'
    set_nombre.admin_order_field = 'mazo__set__nombre'
    
    def tiene_significado_invertido(self, obj):
        """Indica si la carta tiene significado invertido"""
        if obj.significado_invertido and obj.significado_invertido.strip():
            return format_html('<span style="color: #28a745;">✓ Sí</span>')
        return format_html('<span style="color: #dc3545;">✗ No</span>')
    tiene_significado_invertido.short_description = 'Invertido'
    tiene_significado_invertido.boolean = True
    
    # Filtros personalizados
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mazo', 'mazo__set')
    
    # Acciones personalizadas
    actions = ['completar_significados_invertidos', 'limpiar_significados_invertidos']
    
    def completar_significados_invertidos(self, request, queryset):
        """Agregar significado invertido genérico a cartas que no lo tienen"""
        actualizadas = 0
        for carta in queryset:
            if not carta.significado_invertido or not carta.significado_invertido.strip():
                carta.significado_invertido = f"Versión bloqueada o distorsionada de: {carta.significado_normal[:100]}..."
                carta.save()
                actualizadas += 1
        
        if actualizadas > 0:
            self.message_user(request, f'Se completaron {actualizadas} significado{"s" if actualizadas != 1 else ""} invertido{"s" if actualizadas != 1 else ""}.')
        else:
            self.message_user(request, 'Todas las cartas seleccionadas ya tienen significado invertido.', level='INFO')
    completar_significados_invertidos.short_description = "Completar significados invertidos"
    
    def limpiar_significados_invertidos(self, request, queryset):
        """Limpiar significados invertidos de cartas seleccionadas"""
        actualizadas = queryset.update(significado_invertido='')
        self.message_user(request, f'Se limpiaron {actualizadas} significado{"s" if actualizadas != 1 else ""} invertido{"s" if actualizadas != 1 else ""}.')
    limpiar_significados_invertidos.short_description = "Limpiar significados invertidos"


# Personalización del sitio admin
admin.site.site_header = 'Administración Tarotnaútica'
admin.site.site_title = 'Admin Tarotnaútica'
admin.site.index_title = 'Panel de Control - Tarotnaútica'