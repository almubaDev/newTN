from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from oraculo.models import Mazo

class TarotProduct(models.Model):
    """
    Modelo para productos de tarot en la tienda - CON MÉTODOS SEGUROS
    """
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('agotado', 'Agotado'),
        ('proximamente', 'Próximamente'),
    ]
    
    mazo = models.OneToOneField(
        Mazo,
        on_delete=models.CASCADE,
        related_name='producto',
        verbose_name="Mazo asociado",
        help_text="Mazo que se vende en este producto"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio",
        help_text="Precio del producto en la moneda local"
    )
    precio_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name="Precio de Oferta",
        help_text="Precio con descuento (opcional)"
    )
    link_compra = models.URLField(
        verbose_name="Link de Compra",
        help_text="URL donde se procesa el pago del producto",
        max_length=500
    )
    descripcion_adicional = models.TextField(
        blank=True,
        verbose_name="Descripción Adicional",
        help_text="Información extra sobre el producto (opcional)"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name="Estado del Producto"
    )
    destacado = models.BooleanField(
        default=False,
        verbose_name="Producto Destacado",
        help_text="Marcar para mostrar en la sección de destacados"
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden de Aparición",
        help_text="Número para ordenar productos (menor número aparece primero)"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto de Tarot"
        verbose_name_plural = "Productos de Tarot"
        ordering = ['orden', '-destacado', '-fecha_creacion']
    
    def __str__(self):
        try:
            return f"{self.mazo.nombre} - ${self.precio_actual}"
        except:
            return f"Producto {self.id} - ${self.precio_actual}"
    
    # ============== PROPIEDADES SEGURAS ============== #
    
    @property
    def nombre_mazo(self):
        """Nombre del mazo de forma segura"""
        try:
            return self.mazo.nombre
        except:
            return f"Mazo no disponible (ID: {self.mazo_id})"
    
    @property
    def precio_actual(self):
        """Retorna el precio de oferta si existe, sino el precio normal"""
        return self.precio_oferta if self.precio_oferta else self.precio
    
    @property
    def tiene_descuento(self):
        """Verifica si el producto tiene descuento activo"""
        return bool(self.precio_oferta and self.precio_oferta < self.precio)
    
    @property
    def porcentaje_descuento(self):
        """Calcula el porcentaje de descuento"""
        if self.tiene_descuento:
            descuento = ((self.precio - self.precio_oferta) / self.precio) * 100
            return round(descuento, 0)
        return 0
    
    @property
    def esta_disponible(self):
        """Verifica si el producto está disponible para compra"""
        return self.estado == 'activo'
    
    # ============== MÉTODOS SEGUROS ============== #
    
    def get_primeras_cartas(self, cantidad=5):
        """Retorna las primeras N cartas del mazo para mostrar en galería"""
        try:
            if hasattr(self, 'mazo') and self.mazo:
                return self.mazo.cartas.all().order_by('numero')[:cantidad]
        except:
            pass
        return []
    
    def get_total_cartas(self):
        """Retorna el total de cartas del mazo de forma segura"""
        try:
            if hasattr(self, 'mazo') and self.mazo:
                return self.mazo.total_cartas()
        except:
            pass
        return 0
    
    def get_set_nombre(self):
        """Retorna el nombre del set de forma segura"""
        try:
            if hasattr(self, 'mazo') and self.mazo and hasattr(self.mazo, 'set'):
                return self.mazo.set.nombre
        except:
            pass
        return "Set no disponible"
    
    def get_codigo_mazo(self):
        """Retorna el código del mazo de forma segura"""
        try:
            if hasattr(self, 'mazo') and self.mazo:
                return self.mazo.codigo
        except:
            pass
        return "N/A"