from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)
from .models import CustomUser

class CustomRegisterView(CreateView):
    """
    Vista para registro de usuarios
    """
    form_class = CustomUserCreationForm
    template_name = 'user/register.html'
    success_url = reverse_lazy('user:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Auto-login después del registro
        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)
            messages.success(
                self.request, 
                f'¡Bienvenido {user.nombre}! Has recibido 5 créditos de bienvenida.'
            )
            return redirect('oraculo:index')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Cuenta'
        return context


class CustomLoginView(LoginView):
    """
    Vista personalizada para login
    """
    form_class = CustomAuthenticationForm
    template_name = 'user/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('oraculo:index')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'¡Bienvenido de nuevo, {form.get_user().nombre}!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar Sesión'
        return context


class CustomPasswordChangeView(PasswordChangeView):
    """
    Vista para cambiar contraseña
    """
    form_class = CustomPasswordChangeForm
    template_name = 'user/password_change.html'
    success_url = reverse_lazy('user:password_change_done')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tu contraseña ha sido cambiada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cambiar Contraseña'
        return context


class CustomPasswordResetView(PasswordResetView):
    """
    Vista para solicitar reset de contraseña
    """
    form_class = CustomPasswordResetForm
    template_name = 'user/password_reset.html'
    success_url = reverse_lazy('user:password_reset_done')
    email_template_name = 'user/password_reset_email.html'
    subject_template_name = 'user/password_reset_subject.txt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Recuperar Contraseña'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Vista para confirmar reset de contraseña
    """
    form_class = CustomSetPasswordForm
    template_name = 'user/password_reset_confirm.html'
    success_url = reverse_lazy('user:password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Establecer Nueva Contraseña'
        return context


@login_required
def profile_view(request):
    """
    Vista del perfil del usuario
    """
    context = {
        'title': 'Mi Perfil',
        'user': request.user
    }
    return render(request, 'user/profile.html', context)


def password_change_done_view(request):
    """
    Vista que confirma que la contraseña fue cambiada
    """
    context = {'title': 'Contraseña Cambiada'}
    return render(request, 'user/password_change_done.html', context)


def password_reset_done_view(request):
    """
    Vista que confirma que se envió el email de reset
    """
    context = {'title': 'Email Enviado'}
    return render(request, 'user/password_reset_done.html', context)


def password_reset_complete_view(request):
    """
    Vista que confirma que el reset fue completado
    """
    context = {'title': 'Contraseña Restablecida'}
    return render(request, 'user/password_reset_complete.html', context)