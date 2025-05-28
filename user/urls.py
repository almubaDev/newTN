from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'user'

urlpatterns = [
    # Autenticación
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    
    # Perfil
    path('profile/', views.profile_view, name='profile'),
    
    # Cambio de contraseña
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', views.password_change_done_view, name='password_change_done'),
    
    # Reset de contraseña
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.password_reset_complete_view, name='password_reset_complete'),
]