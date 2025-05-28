from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from oraculo.models import Mazo

class TarotProduct(models.Model):
    """
    Modelo para productos de tarot en la tienda
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
        return f"{self.mazo.nombre} - ${self.precio_actual}"
    
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
    
    def get_primeras_cartas(self, cantidad=5):
        """Retorna las primeras N cartas del mazo para mostrar en galería"""
        return self.mazo.cartas.all().order_by('numero')[:cantidad]