from django.db import models
from user.models import CustomUser
from tienda.models import TarotProduct
from django.utils import timezone

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