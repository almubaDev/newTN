from django.db import models
from django.core.validators import MinValueValidator

class Set(models.Model):
    """
    Modelo para agrupar diferentes mazos de cartas
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Set")
    descripcion = models.TextField(verbose_name="Descripción")
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Código único",
        help_text="Código único para identificar el set"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Set de Cartas"
        verbose_name_plural = "Sets de Cartas"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Mazo(models.Model):
    """
    Modelo para mazos de cartas individuales
    """
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Mazo")
    descripcion = models.TextField(verbose_name="Descripción")
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Código único",
        help_text="Código único para identificar el mazo"
    )
    imagen_reverso = models.ImageField(
        upload_to='mazos/reversos/', 
        verbose_name="Imagen del Reverso",
        help_text="Imagen que se muestra en el reverso de todas las cartas de este mazo"
    )
    set = models.ForeignKey(
        Set, 
        on_delete=models.CASCADE, 
        related_name='mazos',
        verbose_name="Set al que pertenece"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mazo"
        verbose_name_plural = "Mazos"
        ordering = ['set', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.set.nombre}"
    
    def total_cartas(self):
        """Retorna el número total de cartas en este mazo"""
        return self.cartas.count()


class Carta(models.Model):
    """
    Modelo para cartas individuales
    """
    numero = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Número",
        help_text="Número de orden de la carta en el mazo"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Carta")
    imagen = models.ImageField(
        upload_to='cartas/', 
        verbose_name="Imagen de la Carta"
    )
    significado_normal = models.TextField(
        verbose_name="Significado Normal",
        help_text="Significado cuando la carta aparece en posición normal"
    )
    significado_invertido = models.TextField(
        verbose_name="Significado Invertido",
        help_text="Significado cuando la carta aparece invertida"
    )
    mazo = models.ForeignKey(
        Mazo, 
        on_delete=models.CASCADE, 
        related_name='cartas',
        verbose_name="Mazo al que pertenece"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Carta"
        verbose_name_plural = "Cartas"
        ordering = ['mazo', 'numero']
        unique_together = ['numero', 'mazo']  # Evita números duplicados en el mismo mazo
    
    def __str__(self):
        return f"{self.numero}. {self.nombre} - {self.mazo.nombre}"
    
    def get_significado(self, invertida=False):
        """
        Retorna el significado apropiado según si la carta está invertida o no
        """
        return self.significado_invertido if invertida else self.significado_normal