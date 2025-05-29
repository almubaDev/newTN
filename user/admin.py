from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario para crear usuarios en el admin
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'nombre')

class CustomUserChangeForm(UserChangeForm):
    """
    Formulario para editar usuarios en el admin
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'nombre', 'creditos_disponibles', 'is_active', 'is_staff')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Configuración del admin para usuarios personalizados
    """
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # Campos mostrados en la lista
    list_display = ('email', 'nombre', 'creditos_disponibles', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'nombre')
    ordering = ('-date_joined',)
    
    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('nombre',)
        }),
        ('Créditos', {
            'fields': ('creditos_disponibles',)
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Configuración para agregar usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'creditos_disponibles'),
        }),
    )
    
    # Campos de solo lectura
    readonly_fields = ('date_joined', 'last_login', 'last_updated')
    
    # Acciones personalizadas
    # actions = ['dar_creditos_bienvenida', 'resetear_creditos']
    
    # # def dar_creditos_bienvenida(self, request, queryset):
    # #     """Acción para dar 5 créditos de bienvenida"""
    # #     for user in queryset:
    # #         user.agregar_creditos(5.00)
    # #     self.message_user(request, f'Se han agregado 5 créditos a {queryset.count()} usuarios.')
    # # dar_creditos_bienvenida.short_description = "Dar 5 créditos de bienvenida"
    
    # def resetear_creditos(self, request, queryset):
    #     """Acción para resetear créditos a 0"""
    #     queryset.update(creditos_disponibles=0.00)
    #     self.message_user(request, f'Se han reseteado los créditos de {queryset.count()} usuarios.')
    # resetear_creditos.short_description = "Resetear créditos a 0"