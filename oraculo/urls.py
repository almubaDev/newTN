from django.urls import path
from . import views

app_name = 'oraculo'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='index'),
    path('motor-nautica/', views.motor_nautica, name='motor_nautica'),
    
    # ============== ADMIN DASHBOARD ============== #
    path('dashmid/', views.admin_dashboard, name='admin_dashboard'),
    
    # ============== SET URLs ============== #
    path('dashmid/sets/', views.set_list, name='set_list'),
    path('dashmid/sets/crear/', views.set_create, name='set_create'),
    path('dashmid/sets/<int:pk>/', views.set_detail, name='set_detail'),
    path('dashmid/sets/<int:pk>/editar/', views.set_update, name='set_update'),
    path('dashmid/sets/<int:pk>/eliminar/', views.set_delete, name='set_delete'),

    # ============== MAZO URLs ============== #
    path('dashmid/mazos/', views.mazo_list, name='mazo_list'),
    path('dashmid/mazos/crear/', views.mazo_create, name='mazo_create'),
    path('dashmid/mazos/<int:pk>/', views.mazo_detail, name='mazo_detail'),
    path('dashmid/mazos/<int:pk>/editar/', views.mazo_update, name='mazo_update'),
    path('dashmid/mazos/<int:pk>/eliminar/', views.mazo_delete, name='mazo_delete'),
    
    # ============== CARTA URLs ============== #
    # URLs públicas
    path('cartas/', views.carta_list, name='carta_list'),
    path('cartas/<int:pk>/', views.carta_detail, name='carta_detail'),
    
    # URLs administrativas
    path('dashmid/cartas/crear/', views.carta_create, name='carta_create'),
    path('dashmid/cartas/<int:pk>/editar/', views.carta_update, name='carta_update'),
    path('dashmid/cartas/<int:pk>/eliminar/', views.carta_delete, name='carta_delete'),
    
    # ============== AJAX URLs ============== #
    path('ajax/mazos-por-set/', views.get_mazos_by_set, name='get_mazos_by_set'),
]