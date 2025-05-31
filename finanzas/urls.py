# finanzas/urls.py - URLS ACTUALIZADAS CON DEBUG
from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    # ============== CARRITO TRADICIONAL ============== #
    # Carrito principal
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    
    # Operaciones AJAX del carrito
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    
    # Checkout tradicional
    path('checkout/', views.resumen_checkout, name='checkout'),
    
    # Widget AJAX
    path('api/carrito-widget/', views.carrito_widget, name='carrito_widget'),
    
    # ============== INTEGRACIÓN PAYPAL ============== #
    # Crear orden PayPal
    path('paypal/crear-orden/', views.crear_orden_paypal, name='crear_orden_paypal'),
    
    # Webhook PayPal (sin login requerido)
    path('webhook/paypal/', views.webhook_paypal, name='webhook_paypal'),
    
    # URLs de retorno PayPal
    path('pago-exitoso/<str:codigo_orden>/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-cancelado/<str:codigo_orden>/', views.pago_cancelado, name='pago_cancelado'),
    
    # ============== DEBUG PAYPAL (Solo en DEBUG mode) ============== #
    path('debug/paypal/', views.debug_paypal, name='debug_paypal'),
    path('debug/test-connection/', views.test_paypal_connection, name='test_paypal_connection'),
    
    # ============== DASHBOARD DE FINANZAS ============== #
    # Dashboard principal (solo staff)
    path('dashboard/', views.dashboard_finanzas, name='dashboard'),
    
    # Reportes detallados
    path('reportes/', views.reportes_detallados, name='reportes'),
    
    # Exportar datos
    path('exportar/ventas-csv/', views.exportar_ventas_csv, name='exportar_ventas_csv'),
    
    # API para métricas en tiempo real
    path('api/metricas-tiempo-real/', views.api_metricas_tiempo_real, name='api_metricas_tiempo_real'),
]