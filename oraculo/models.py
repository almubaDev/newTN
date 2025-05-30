from django.db import models
from django.core.validators import MinValueValidator
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def upload_to_cartas(instance, filename):
    """Función personalizada para mantener el nombre original y preservar formato"""
    return f'cartas/{filename}'

def upload_to_mazos_reversos(instance, filename):
    """Función personalizada para reversos de mazos"""
    return f'mazos/reversos/{filename}'

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
        help_text="Código único para identificar el set",
        )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Set de Cartas"
        verbose_name_plural = "Sets de Cartas"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    def productos_activos_count(self):
        """Retorna el número de productos activos en este set"""
        return self.mazos.filter(producto__estado='activo').count()


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
        upload_to=upload_to_mazos_reversos, 
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
    
    def save(self, *args, **kwargs):
        """
        Override del método save para aplanar automáticamente imágenes PNG multicapa en reversos
        """
        # Procesar imagen de reverso solo si es nueva o cambió
        if self.imagen_reverso and hasattr(self.imagen_reverso, 'file'):
            # Verificar si es PNG y procesarlo
            if self.imagen_reverso.name.lower().endswith('.png'):
                # Abrir imagen con PIL
                image = Image.open(self.imagen_reverso.file)
                
                # Si tiene transparencia (RGBA), aplanar contra fondo blanco
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    # Crear fondo blanco del mismo tamaño
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    
                    # Si es RGBA, usar alpha compositing
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])  # usar canal alpha como máscara
                    else:
                        # Convertir a RGBA primero
                        image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1])
                    
                    # La imagen aplanada
                    flattened_image = background
                else:
                    # Si no tiene transparencia, convertir a RGB
                    flattened_image = image.convert('RGB')
                
                # Guardar en memoria como PNG aplanado
                output = io.BytesIO()
                flattened_image.save(output, format='PNG', optimize=False, compress_level=0)
                output.seek(0)
                
                # Crear nuevo archivo en memoria
                self.imagen_reverso = InMemoryUploadedFile(
                    output, 'ImageField', 
                    self.imagen_reverso.name, 
                    'image/png',
                    sys.getsizeof(output), 
                    None
                )
        
        # Llamar al save original
        super().save(*args, **kwargs)


def upload_to_complementos_instructivos(instance, filename):
    """Función personalizada para instructivos de mazos"""
    return f'complementos/instructivos/{filename}'

def upload_to_complementos_plantillas(instance, filename):
    """Función personalizada para plantillas de impresión de mazos"""
    return f'complementos/plantillas/{filename}'


class ComplementosMazo(models.Model):
    """
    Modelo para archivos complementarios de un mazo (instructivos y plantillas)
    """
    mazo = models.OneToOneField(
        Mazo,
        on_delete=models.CASCADE,
        related_name='complementos',
        verbose_name="Mazo"
    )
    
    instructivo = models.FileField(
        upload_to=upload_to_complementos_instructivos,
        blank=True,
        null=True,
        verbose_name="Instructivo",
        help_text="Archivo con las instrucciones de uso del mazo (PDF, DOC, etc.)"
    )
    
    plantilla_impresion = models.FileField(
        upload_to=upload_to_complementos_plantillas,
        blank=True,
        null=True,
        verbose_name="Plantilla de Impresión",
        help_text="Archivo con plantilla para imprimir el mazo (PDF, AI, PSD, etc.)"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Complementos de Mazo"
        verbose_name_plural = "Complementos de Mazos"
    
    def __str__(self):
        return f"Complementos de {self.mazo.nombre}"
    
    def tiene_instructivo(self):
        """Verifica si tiene instructivo"""
        return bool(self.instructivo and self.instructivo.name)
    
    def tiene_plantilla(self):
        """Verifica si tiene plantilla de impresión"""
        return bool(self.plantilla_impresion and self.plantilla_impresion.name)
    
    def get_instructivo_extension(self):
        """Retorna la extensión del archivo instructivo"""
        if self.tiene_instructivo():
            return self.instructivo.name.split('.')[-1].upper() if '.' in self.instructivo.name else 'ARCHIVO'
        return None
    
    def get_plantilla_extension(self):
        """Retorna la extensión del archivo de plantilla"""
        if self.tiene_plantilla():
            return self.plantilla_impresion.name.split('.')[-1].upper() if '.' in self.plantilla_impresion.name else 'ARCHIVO'
        return None
    
    def get_instructivo_size(self):
        """Retorna el tamaño del instructivo en formato legible"""
        if self.tiene_instructivo():
            try:
                size = self.instructivo.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            except:
                return "Tamaño desconocido"
        return None
    
    def get_plantilla_size(self):
        """Retorna el tamaño de la plantilla en formato legible"""
        if self.tiene_plantilla():
            try:
                size = self.plantilla_impresion.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            except:
                return "Tamaño desconocido"
        return None
    
    def tiene_complementos(self):
        """Verifica si tiene algún complemento"""
        return self.tiene_instructivo() or self.tiene_plantilla()
    
    def count_complementos(self):
        """Cuenta cuántos complementos tiene"""
        count = 0
        if self.tiene_instructivo():
            count += 1
        if self.tiene_plantilla():
            count += 1
        return count
    

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
        upload_to=upload_to_cartas,
        verbose_name="Imagen de la Carta"
    )
    significado_normal = models.TextField(
        verbose_name="Significado Normal",
        help_text="Significado cuando la carta aparece en posición normal"
    )
    significado_invertido = models.TextField(
        verbose_name="Significado Invertido",
        help_text="Significado cuando la carta aparece invertida (opcional)",
        blank=True,
        null=True
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
        unique_together = ['numero', 'mazo']
    
    def __str__(self):
        return f"{self.numero}. {self.nombre} - {self.mazo.nombre}"
    
    def get_significado(self, invertida=False):
        """
        Retorna el significado apropiado según si la carta está invertida o no
        """
        if invertida and self.significado_invertido:
            return self.significado_invertido
        return self.significado_normal
    
    def tiene_significado_invertido(self):
        """
        Verifica si la carta tiene significado invertido definido
        """
        return bool(self.significado_invertido and self.significado_invertido.strip())
    
    def save(self, *args, **kwargs):
        """
        Override del método save para aplanar automáticamente imágenes PNG multicapa
        """
        # Procesar imagen solo si es nueva o cambió
        if self.imagen and hasattr(self.imagen, 'file'):
            # Verificar si es PNG y procesarlo
            if self.imagen.name.lower().endswith('.png'):
                # Abrir imagen con PIL
                image = Image.open(self.imagen.file)
                
                # Si tiene transparencia (RGBA), aplanar contra fondo blanco
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    # Crear fondo blanco del mismo tamaño
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    
                    # Si es RGBA, usar alpha compositing
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])  # usar canal alpha como máscara
                    else:
                        # Convertir a RGBA primero
                        image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1])
                    
                    # La imagen aplanada
                    flattened_image = background
                else:
                    # Si no tiene transparencia, convertir a RGB
                    flattened_image = image.convert('RGB')
                
                # Guardar en memoria como PNG aplanado
                output = io.BytesIO()
                flattened_image.save(output, format='PNG', optimize=False, compress_level=0)
                output.seek(0)
                
                # Crear nuevo archivo en memoria
                self.imagen = InMemoryUploadedFile(
                    output, 'ImageField', 
                    self.imagen.name, 
                    'image/png',
                    sys.getsizeof(output), 
                    None
                )
        
        # Llamar al save original
        super().save(*args, **kwargs)