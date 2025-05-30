from django.db import models
from user.models import CustomUser
from tienda.models import TarotProduct
from django.utils import timezone
import uuid

# ============== MODELOS EXISTENTES DEL CARRITO ============== #

class Carrito(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Carrito de {self.usuario.username}"
    
    @property
    def total_items(self):
        return sum(item.cantidad for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total(self):
        # Aquí puedes agregar impuestos, descuentos, etc.
        return self.subtotal
    
    def limpiar(self):
        """Vacía completamente el carrito"""
        self.items.all().delete()

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(TarotProduct, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['carrito', 'producto']
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.mazo.nombre}"
    
    @property
    def precio_unitario(self):
        return self.producto.precio_actual
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


# ============== NUEVOS MODELOS PARA PAYPAL ============== #

class OrdenCompra(models.Model):
    """
    Modelo para órdenes de compra (antes y después del pago)
    """
    ESTADO_CHOICES = [
        ('creada', 'Creada'),
        ('pendiente', 'Pendiente de Pago'),
        ('aprobada', 'Aprobada por PayPal'),
        ('pagada', 'Pago Completado'),
        ('cancelada', 'Cancelada'),
        ('reembolsada', 'Reembolsada'),
        ('error', 'Error en Pago'),
    ]
    
    # Información básica
    usuario = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='ordenes_compra'
    )
    codigo_orden = models.CharField(
        max_length=50, 
        unique=True, 
        default=uuid.uuid4,
        verbose_name="Código de Orden"
    )
    
    # PayPal tracking
    paypal_order_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="ID de Orden PayPal"
    )
    paypal_payment_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="ID de Pago PayPal"
    )
    
    # Estado y montos
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='creada'
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Subtotal"
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Total a Pagar"
    )
    moneda = models.CharField(
        max_length=3, 
        default='USD',
        verbose_name="Moneda"
    )
    
    # Datos adicionales del pago
    email_paypal = models.EmailField(
        blank=True, 
        null=True,
        verbose_name="Email PayPal del Comprador"
    )
    datos_paypal = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Datos Completos de PayPal"
    )
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Pago Completado"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Orden {self.codigo_orden} - {self.usuario.username} (${self.total})"
    
    @property
    def esta_pagada(self):
        """Verifica si la orden está completamente pagada"""
        return self.estado in ['pagada', 'aprobada']
    
    @property
    def puede_procesar(self):
        """Verifica si se pueden crear las compras de productos"""
        return self.estado == 'pagada'
    
    def crear_compras_productos(self):
        """
        Crea los CompraProducto después de confirmar el pago
        """
        if not self.puede_procesar:
            return False
        
        from tienda.models import CompraProducto
        
        compras_creadas = []
        
        for item in self.items.all():
            # Verificar si ya existe una compra para este producto
            compra_existente = CompraProducto.objects.filter(
                usuario=self.usuario,
                producto=item.producto
            ).first()
            
            if not compra_existente:
                compra = CompraProducto.objects.create(
                    usuario=self.usuario,
                    producto=item.producto,
                    precio_pagado=item.precio_unitario,
                    metodo_pago='paypal',
                    estado='completada',
                    referencia_pago=self.paypal_payment_id or self.paypal_order_id,
                    notas_admin=f'Compra automática desde orden {self.codigo_orden}'
                )
                compras_creadas.append(compra)
        
        return compras_creadas
    
    def vaciar_carrito_usuario(self):
        """
        Vacía el carrito del usuario después de completar la compra
        """
        try:
            carrito = self.usuario.carrito
            carrito.limpiar()
            return True
        except:
            return False


class ItemOrden(models.Model):
    """
    Items individuales de una orden de compra
    """
    orden = models.ForeignKey(
        OrdenCompra, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    producto = models.ForeignKey(
        TarotProduct, 
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Precio Unitario"
    )
    
    class Meta:
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"
        unique_together = ['orden', 'producto']
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.mazo.nombre} (Orden {self.orden.codigo_orden})"
    
    @property
    def subtotal(self):
        """Subtotal del item (cantidad × precio unitario)"""
        return self.cantidad * self.precio_unitario
    
    @property
    def nombre_producto(self):
        """Nombre del producto de forma segura"""
        try:
            return self.producto.mazo.nombre
        except:
            return f"Producto ID: {self.producto_id}"


class LogWebhookPayPal(models.Model):
    """
    Log de webhooks recibidos de PayPal para debugging
    """
    webhook_id = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    orden_relacionada = models.ForeignKey(
        OrdenCompra, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    datos_completos = models.JSONField(default=dict)
    procesado = models.BooleanField(default=False)
    error_mensaje = models.TextField(blank=True)
    fecha_recibido = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log Webhook PayPal"
        verbose_name_plural = "Logs Webhooks PayPal"
        ordering = ['-fecha_recibido']
    
    def __str__(self):
        return f"Webhook {self.event_type} - {self.fecha_recibido.strftime('%d/%m/%Y %H:%M')}"