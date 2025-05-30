# 4. finanzas/urls.py
from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    # Carrito principal
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    
    # Operaciones AJAX del carrito
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    
    # Checkout
    path('checkout/', views.resumen_checkout, name='checkout'),
    
    # Widget AJAX
    path('api/carrito-widget/', views.carrito_widget, name='carrito_widget'),
]