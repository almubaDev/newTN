from django.urls import path
from . import views

app_name = 'tienda'

urlpatterns = [
    # ============== VISTAS PÚBLICAS ============== #
    # Tienda principal
    path('', views.tienda_home, name='home'),
    
    # Catálogo público de productos
    path('productos/', views.producto_list, name='producto_list'),
    
    # Detalle público de producto
    path('producto/<int:pk>/', views.producto_detail, name='producto_detail'),
    
    # ============== VISTAS ADMINISTRATIVAS ============== #
    # Lista administrativa de productos
    path('admin/productos/', views.admin_producto_list, name='admin_producto_list'),
    
    # CRUD de productos
    path('admin/productos/crear/', views.admin_producto_create, name='admin_producto_create'),
    path('admin/productos/<int:pk>/', views.admin_producto_detail, name='admin_producto_detail'),
    path('admin/productos/<int:pk>/editar/', views.admin_producto_update, name='admin_producto_update'),
    path('admin/productos/<int:pk>/eliminar/', views.admin_producto_delete, name='admin_producto_delete'),
    
    
    # ============== COMPRAS DE USUARIOS ============== #
    # Mis compras (usuario logueado)
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    
    # Detalle de una compra específica
    path('compra/<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
]