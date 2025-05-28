from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo de usuario
    """
    def create_user(self, email, nombre, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email y contraseña dados
        """
        if not email:
            raise ValueError('El usuario debe tener un email')
        if not nombre:
            raise ValueError('El usuario debe tener un nombre')
        
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con email y contraseña dados
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        return self.create_user(email, nombre, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado que usa email en lugar de username
    """
    email = models.EmailField(
        unique=True,
        verbose_name="Correo Electrónico",
        help_text="Dirección de correo único para iniciar sesión"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre Completo",
        help_text="Nombre completo del usuario"
    )
    creditos_disponibles = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Créditos Disponibles",
        help_text="Créditos disponibles para usar en la plataforma"
    )
    
    # Campos administrativos
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Es Staff")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.nombre} ({self.email})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        return self.nombre
    
    def get_short_name(self):
        """Retorna el nombre completo del usuario"""
        return self.nombre
    
    def tiene_creditos_suficientes(self, cantidad):
        """Verifica si el usuario tiene suficientes créditos"""
        return self.creditos_disponibles >= Decimal(str(cantidad))
    
    def consumir_creditos(self, cantidad):
        """Consume una cantidad de créditos del usuario"""
        cantidad_decimal = Decimal(str(cantidad))
        if self.tiene_creditos_suficientes(cantidad_decimal):
            self.creditos_disponibles -= cantidad_decimal
            self.save(update_fields=['creditos_disponibles'])
            return True
        return False
    
    def agregar_creditos(self, cantidad):
        """Agrega créditos al usuario"""
        self.creditos_disponibles += Decimal(str(cantidad))
        self.save(update_fields=['creditos_disponibles'])