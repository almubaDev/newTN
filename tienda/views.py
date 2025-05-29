from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import TarotProduct
from .forms import TarotProductForm

# Helper function
def is_staff_user(user):
    """Helper function to check if user is staff"""
    return user.is_authenticated and user.is_staff

# ============== VISTAS ADMINISTRATIVAS ============== #

@user_passes_test(lambda u: u.is_staff)
def admin_producto_list(request):
    """
    Lista administrativa de productos
    """
    productos = TarotProduct.objects.select_related('mazo', 'mazo__set').all()
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        productos = productos.filter(
            Q(mazo__nombre__icontains=search) |
            Q(mazo__set__nombre__icontains=search) |
            Q(descripcion_adicional__icontains=search)
        )
    
    # Filtro por estado
    estado_filter = request.GET.get('estado')
    if estado_filter:
        productos = productos.filter(estado=estado_filter)
    
    # Paginación
    paginator = Paginator(productos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Administrar Productos',
        'page_obj': page_obj,
        'search': search,
        'estado_filter': estado_filter,
        'estados': TarotProduct.ESTADO_CHOICES,
    }
    return render(request, 'tienda/admin/producto_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_producto_create(request):
    """
    Crear nuevo producto - CORREGIDO
    """
    if request.method == 'POST':
        form = TarotProductForm(request.POST)
        print(f"POST recibido, form data: {request.POST}")  # DEBUG
        
        if form.is_valid():
            try:
                producto = form.save()
                print(f"Producto creado exitosamente: {producto}")  # DEBUG
                messages.success(request, f'Producto "{producto.mazo.nombre}" creado exitosamente.')
                return redirect('tienda:admin_producto_detail', pk=producto.pk)
            except Exception as e:
                print(f"Error al guardar producto: {e}")  # DEBUG
                messages.error(request, f'Error al crear el producto: {str(e)}')
        else:
            # DEBUG: Mostrar errores del formulario
            print(f"Formulario no válido. Errores: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TarotProductForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Producto',
        'action': 'Crear'
    }
    return render(request, 'tienda/admin/producto_form.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_producto_detail(request, pk):
    """
    Detalle administrativo de producto
    """
    producto = get_object_or_404(
        TarotProduct.objects.select_related('mazo', 'mazo__set'),
        pk=pk
    )
    
    context = {
        'producto': producto,
        'title': f'Producto: {producto.mazo.nombre}',
        'cartas_muestra': producto.get_primeras_cartas(3),
    }
    return render(request, 'tienda/admin/producto_detail.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_producto_update(request, pk):
    """
    Actualizar producto existente - CORREGIDO
    """
    producto = get_object_or_404(TarotProduct, pk=pk)
    
    if request.method == 'POST':
        form = TarotProductForm(request.POST, instance=producto)
        print(f"POST recibido para actualizar, form data: {request.POST}")  # DEBUG
        
        if form.is_valid():
            try:
                producto = form.save()
                print(f"Producto actualizado exitosamente: {producto}")  # DEBUG
                messages.success(request, f'Producto "{producto.mazo.nombre}" actualizado exitosamente.')
                return redirect('tienda:admin_producto_detail', pk=producto.pk)
            except Exception as e:
                print(f"Error al actualizar producto: {e}")  # DEBUG
                messages.error(request, f'Error al actualizar el producto: {str(e)}')
        else:
            # DEBUG: Mostrar errores del formulario
            print(f"Formulario no válido. Errores: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TarotProductForm(instance=producto)
    
    context = {
        'form': form,
        'producto': producto,
        'title': f'Editar: {producto.mazo.nombre}',
        'action': 'Actualizar'
    }
    return render(request, 'tienda/admin/producto_form.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_producto_delete(request, pk):
    """
    Eliminar producto
    """
    producto = get_object_or_404(TarotProduct, pk=pk)
    
    if request.method == 'POST':
        nombre = producto.mazo.nombre
        try:
            producto.delete()
            messages.success(request, f'Producto "{nombre}" eliminado exitosamente.')
            return redirect('tienda:admin_producto_list')
        except Exception as e:
            print(f"Error al eliminar producto: {e}")  # DEBUG
            messages.error(request, f'Error al eliminar el producto: {str(e)}')
            return redirect('tienda:admin_producto_detail', pk=producto.pk)
    
    context = {
        'producto': producto,
        'title': f'Eliminar: {producto.mazo.nombre}'
    }
    return render(request, 'tienda/admin/producto_confirm_delete.html', context)

# ============== VISTAS PÚBLICAS ============== #

def tienda_home(request):
    """
    Vista principal de la tienda - con filtros por categorías y sidebar
    """
    productos = TarotProduct.objects.filter(estado='activo').select_related('mazo', 'mazo__set')
    
    # Filtro por categoría (navbar secundaria)
    categoria = request.GET.get('categoria', 'todos')
    if categoria == 'destacados':
        productos = productos.filter(destacado=True)
    elif categoria == 'ofertas':
        productos = productos.filter(precio_oferta__isnull=False)
    elif categoria == 'recientes':
        productos = productos.order_by('-fecha_creacion')
    # Si es 'todos' o cualquier otro valor, no filtrar
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        productos = productos.filter(
            Q(mazo__nombre__icontains=search) |
            Q(mazo__set__nombre__icontains=search) |
            Q(descripcion_adicional__icontains=search)
        )
    
    # Filtro por sets múltiples (checkboxes)
    sets_filter = request.GET.getlist('sets')  # Obtener lista de sets seleccionados
    if sets_filter:
        productos = productos.filter(mazo__set_id__in=sets_filter)
    
    # Ordenamiento (solo si no es categoría 'recientes' que ya está ordenada)
    orden = request.GET.get('orden', 'destacados')
    if categoria != 'recientes':
        if orden == 'precio_asc':
            productos = productos.order_by('precio')
        elif orden == 'precio_desc':
            productos = productos.order_by('-precio')
        elif orden == 'nombre':
            productos = productos.order_by('mazo__nombre')
        elif orden == 'recientes':
            productos = productos.order_by('-fecha_creacion')
        else:  # destacados (por defecto)
            productos = productos.order_by('orden', '-destacado', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Sets para filtros - TODOS los sets, no solo los que tienen productos
    from oraculo.models import Set
    sets_disponibles = Set.objects.all().order_by('nombre')
    
    context = {
        'title': 'Tienda Tarotnaútica',
        'page_obj': page_obj,
        'sets_disponibles': sets_disponibles,
        'search': search,
        'sets_filter': sets_filter,  # Lista de sets seleccionados
        'orden': orden,
        'categoria': categoria,
        'total_productos': page_obj.paginator.count,
    }
    
    return render(request, 'tienda/home.html', context)
            

def producto_list(request):
    """
    Lista pública de productos (mantener para compatibilidad)
    """
    productos = TarotProduct.objects.filter(estado='activo').select_related('mazo', 'mazo__set')
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        productos = productos.filter(
            Q(mazo__nombre__icontains=search) |
            Q(mazo__set__nombre__icontains=search) |
            Q(descripcion_adicional__icontains=search)
        )
    
    # Filtro por set
    set_filter = request.GET.get('set')
    if set_filter:
        productos = productos.filter(mazo__set_id=set_filter)
    
    # Filtro por precio
    precio_filter = request.GET.get('precio')
    if precio_filter == 'bajo':
        productos = productos.filter(precio__lte=20)
    elif precio_filter == 'medio':
        productos = productos.filter(precio__gt=20, precio__lte=50)
    elif precio_filter == 'alto':
        productos = productos.filter(precio__gt=50)
    
    # Filtro por ofertas
    if request.GET.get('ofertas'):
        productos = productos.filter(precio_oferta__isnull=False)
    
    # Ordenamiento
    orden = request.GET.get('orden', 'destacados')
    if orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio')
    elif orden == 'nombre':
        productos = productos.order_by('mazo__nombre')
    elif orden == 'recientes':
        productos = productos.order_by('-fecha_creacion')
    else:  # destacados (por defecto)
        productos = productos.order_by('orden', '-destacado', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Sets para filtros
    from oraculo.models import Set
    sets_disponibles = Set.objects.filter(
        mazos__producto__estado='activo'
    ).distinct()
    
    context = {
        'title': 'Catálogo de Productos',
        'page_obj': page_obj,
        'sets_disponibles': sets_disponibles,
        'search': search,
        'set_filter': set_filter,
        'precio_filter': precio_filter,
        'orden': orden,
        'total_productos': page_obj.paginator.count,
    }
    
    return render(request, 'tienda/producto_list.html', context)

def producto_detail(request, pk):
    """
    Detalle público de producto
    """
    producto = get_object_or_404(
        TarotProduct.objects.select_related('mazo', 'mazo__set'),
        pk=pk,
        estado='activo'
    )
    
    # Primeras 5 cartas para la galería
    cartas_galeria = producto.get_primeras_cartas(5)
    
    # Productos relacionados del mismo set
    productos_relacionados = TarotProduct.objects.filter(
        mazo__set=producto.mazo.set,
        estado='activo'
    ).exclude(pk=producto.pk).select_related('mazo')[:4]
    
    context = {
        'title': f'{producto.mazo.nombre} - Tienda',
        'producto': producto,
        'cartas_galeria': cartas_galeria,
        'productos_relacionados': productos_relacionados,
        'total_cartas': producto.mazo.total_cartas(),
    }
    
    return render(request, 'tienda/producto_detail.html', context)