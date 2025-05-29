from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario de registro personalizado
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'tu@email.com'
        })
    )
    nombre = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Tu nombre completo'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Contraseña'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Confirmar contraseña'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'nombre', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nombre = self.cleaned_data['nombre']
        # Dar créditos iniciales de bienvenida
        user.creditos_disponibles = 0.00
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulario de login personalizado
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'tu@email.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Contraseña'
        })
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Correo electrónico o contraseña incorrectos.",
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario para cambiar contraseña
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Contraseña actual'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Nueva contraseña'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    """
    Formulario para solicitar reset de contraseña
    """
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'tu@email.com'
        })
    )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Formulario para establecer nueva contraseña después del reset
    """
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Nueva contraseña'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )