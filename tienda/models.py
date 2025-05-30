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
        max_length=500,
        null=True,
        blank=True
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


class CompraProducto(models.Model):
    """
    Modelo para trackear productos comprados por usuarios
    """
    ESTADO_COMPRA_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('reembolsada', 'Reembolsada'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('mercadopago', 'MercadoPago'),
        ('transferencia', 'Transferencia'),
        ('manual', 'Asignación Manual'),
        ('otro', 'Otro'),
    ]
    
    usuario = models.ForeignKey(
        'user.CustomUser',
        on_delete=models.CASCADE,
        related_name='compras',
        verbose_name="Usuario"
    )
    producto = models.ForeignKey(
        TarotProduct,
        on_delete=models.CASCADE,
        related_name='compras',
        verbose_name="Producto"
    )
    precio_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio Pagado",
        help_text="Precio que efectivamente pagó el usuario"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='manual',
        verbose_name="Método de Pago"
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_COMPRA_CHOICES,
        default='completada',
        verbose_name="Estado de la Compra"
    )
    referencia_pago = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Referencia de Pago",
        help_text="ID de transacción, número de referencia, etc."
    )
    notas_admin = models.TextField(
        blank=True,
        verbose_name="Notas del Administrador",
        help_text="Notas internas para el equipo"
    )
    fecha_compra = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Compra"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    
    class Meta:
        verbose_name = "Compra de Producto"
        verbose_name_plural = "Compras de Productos"
        ordering = ['-fecha_compra']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'producto'],
                name='unique_usuario_producto'
            )
        ]
    
    def __str__(self):
        try:
            return f"{self.usuario.nombre} - {self.producto.mazo.nombre} (${self.precio_pagado})"
        except:
            return f"Compra {self.id} - ${self.precio_pagado}"
    
    @property
    def nombre_producto(self):
        """Nombre del producto de forma segura"""
        try:
            return self.producto.mazo.nombre
        except:
            return f"Producto ID: {self.producto_id}"
    
    @property
    def es_completada(self):
        """Verifica si la compra está completada"""
        return self.estado == 'completada'
    
    @property
    def puede_descargar(self):
        """Verifica si el usuario puede descargar el producto"""
        return self.estado in ['completada']
    
    

