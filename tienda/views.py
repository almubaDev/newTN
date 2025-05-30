from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from .models import TarotProduct, CompraProducto
from .forms import TarotProductForm
from oraculo.models import Set

def is_staff_user(user):
    """Helper function to check if user is staff"""
    return user.is_authenticated and user.is_staff

# ============== VISTAS PÚBLICAS ============== #

def tienda_home(request):
    """
    Vista principal de la tienda - CON MANEJO DE ERRORES
    """
    try:
        # Obtener productos activos con relaciones precargadas
        productos = TarotProduct.objects.filter(
            estado='activo'
        ).select_related('mazo', 'mazo__set').prefetch_related('mazo__cartas')
        
        # Filtro por categoría (navbar secundaria)
        categoria = request.GET.get('categoria', 'todos')
        if categoria == 'destacados':
            productos = productos.filter(destacado=True)
        elif categoria == 'ofertas':
            productos = productos.filter(precio_oferta__isnull=False)
        elif categoria == 'recientes':
            productos = productos.order_by('-fecha_creacion')
        
        # Búsqueda
        search = request.GET.get('search')
        if search:
            productos = productos.filter(
                Q(mazo__nombre__icontains=search) |
                Q(mazo__set__nombre__icontains=search) |
                Q(descripcion_adicional__icontains=search)
            )
        
        # Filtro por sets múltiples (checkboxes)
        sets_filter = request.GET.getlist('sets')
        if sets_filter:
            productos = productos.filter(mazo__set_id__in=sets_filter)
        
        # Ordenamiento
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
        
        # Sets disponibles - TODOS los sets
        sets_disponibles = Set.objects.all().order_by('nombre')
        
        context = {
            'title': 'Tienda Tarotnaútica',
            'page_obj': page_obj,
            'sets_disponibles': sets_disponibles,
            'search': search,
            'sets_filter': sets_filter,
            'orden': orden,
            'categoria': categoria,
            'total_productos': paginator.count,
        }
        
        return render(request, 'tienda/home.html', context)
        
    except Exception as e:
        # Log del error para debugging
        print(f"Error en tienda_home: {e}")
        
        # Contexto mínimo de emergencia
        context = {
            'title': 'Tienda Tarotnaútica',
            'page_obj': None,
            'sets_disponibles': Set.objects.all(),
            'error_message': 'Hay un problema con la tienda. Estamos trabajando para solucionarlo.',
            'total_productos': 0,
        }
        return render(request, 'tienda/home.html', context)

def producto_list(request):
    """
    Lista pública de productos - CON MANEJO DE ERRORES
    """
    try:
        productos = TarotProduct.objects.filter(
            estado='activo'
        ).select_related('mazo', 'mazo__set')
        
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
            'total_productos': paginator.count,
        }
        
        return render(request, 'tienda/producto_list.html', context)
        
    except Exception as e:
        print(f"Error en producto_list: {e}")
        
        context = {
            'title': 'Catálogo de Productos',
            'page_obj': None,
            'sets_disponibles': Set.objects.all(),
            'error_message': 'Error al cargar los productos.',
            'total_productos': 0,
        }
        return render(request, 'tienda/producto_list.html', context)

def producto_detail(request, pk):
    """
    Detalle público de producto - CON VALIDACIÓN
    """
    try:
        producto = get_object_or_404(
            TarotProduct.objects.select_related('mazo', 'mazo__set'),
            pk=pk,
            estado='activo'
        )
        
        # Verificar que el mazo existe
        if not hasattr(producto, 'mazo') or not producto.mazo:
            raise Http404("Producto no disponible")
        
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
        
    except TarotProduct.DoesNotExist:
        raise Http404("Producto no encontrado")
    except Exception as e:
        print(f"Error en producto_detail: {e}")
        raise Http404("Error al cargar el producto")

# ============== VISTAS ADMINISTRATIVAS ============== #

@user_passes_test(is_staff_user)
def admin_producto_list(request):
    """
    Lista administrativa de productos - CON MANEJO DE ERRORES
    """
    try:
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
        
    except Exception as e:
        print(f"Error en admin_producto_list: {e}")
        messages.error(request, f'Error al cargar productos: {str(e)}')
        return redirect('tienda:home')

@user_passes_test(is_staff_user)
def admin_producto_create(request):
    """
    Crear nuevo producto - CON DEBUG DETALLADO
    """
    print("\n" + "="*50)
    print("🚀 INICIANDO CREACIÓN DE PRODUCTO")
    print("="*50)
    
    if request.method == 'POST':
        print("📥 REQUEST POST RECIBIDO")
        print(f"POST data: {dict(request.POST)}")
        
        form = TarotProductForm(request.POST)
        print(f"✅ Formulario creado")
        
        # Verificar si el formulario es válido
        is_valid = form.is_valid()
        print(f"🔍 ¿Formulario válido? {is_valid}")
        
        if is_valid:
            print("✅ FORMULARIO VÁLIDO - Guardando...")
            try:
                producto = form.save()
                print(f"🎉 PRODUCTO CREADO EXITOSAMENTE: ID {producto.id}")
                print(f"   - Mazo: {producto.mazo.nombre}")
                print(f"   - Precio: ${producto.precio}")
                
                messages.success(request, f'Producto "{producto.mazo.nombre}" creado exitosamente.')
                return redirect('tienda:admin_producto_detail', pk=producto.pk)
                
            except Exception as e:
                print(f"❌ ERROR AL GUARDAR PRODUCTO: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error al crear el producto: {str(e)}')
        else:
            print("❌ FORMULARIO NO VÁLIDO")
            print(f"Errores del formulario: {form.errors}")
            print(f"Errores generales: {form.non_field_errors()}")
            
            # DEBUG MÁS PROFUNDO - Validar campo por campo
            print("\n🔍 VALIDANDO CADA CAMPO:")
            
            # Verificar cada campo individualmente
            for field_name, field in form.fields.items():
                field_value = form.data.get(field_name)
                print(f"   📋 Campo: {field_name}")
                print(f"      - Valor: {field_value}")
                print(f"      - Requerido: {field.required}")
                print(f"      - Tipo: {type(field)}")
                
                # Intentar validar el campo individualmente
                try:
                    if field_name in form.cleaned_data:
                        print(f"      - ✅ Validado: {form.cleaned_data[field_name]}")
                    else:
                        print(f"      - ❌ No validado")
                except:
                    print(f"      - ❌ Error en validación")
            
            # Mostrar errores detallados por campo
            if form.errors:
                print("\n🔴 ERRORES ESPECÍFICOS:")
                for field_name, field_errors in form.errors.items():
                    print(f"   ❌ Campo '{field_name}': {field_errors}")
                    for error in field_errors:
                        messages.error(request, f'Error en {field_name}: {error}')
            
            # Intentar hacer clean() manualmente para ver qué falla
            print("\n🧪 INTENTANDO VALIDACIÓN MANUAL:")
            try:
                form.full_clean()
                print("   ✅ full_clean() ejecutado")
            except Exception as e:
                print(f"   ❌ Error en full_clean(): {e}")
                import traceback
                traceback.print_exc()
                    
            # Verificar datos específicos
            print("\n🔍 ANÁLISIS DE DATOS:")
            print(f"   - Mazo seleccionado: {request.POST.get('mazo')}")
            print(f"   - Precio: {request.POST.get('precio')}")
            print(f"   - Link compra: {request.POST.get('link_compra')}")
            print(f"   - Estado: {request.POST.get('estado')}")
            
    else:
        print("📄 REQUEST GET - Creando formulario vacío")
        form = TarotProductForm()
        
        # Verificar mazos disponibles
        mazos_disponibles = form.fields['mazo'].queryset
        print(f"🎯 Mazos disponibles para crear producto: {mazos_disponibles.count()}")
        
        if mazos_disponibles.count() == 0:
            print("⚠️  ¡PROBLEMA! No hay mazos disponibles")
            messages.warning(request, 'No hay mazos disponibles para crear productos. Crea un mazo primero.')
        else:
            print("📋 Lista de mazos disponibles:")
            for mazo in mazos_disponibles:
                print(f"   - ID: {mazo.id} | {mazo.nombre} | Set: {mazo.set.nombre}")
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Producto',
        'action': 'Crear'
    }
    
    print("🎨 Renderizando template...")
    print("="*50 + "\n")
    return render(request, 'tienda/admin/producto_form.html', context)

@user_passes_test(is_staff_user)
def admin_producto_detail(request, pk):
    """
    Detalle administrativo de producto - CON VALIDACIÓN
    """
    try:
        producto = get_object_or_404(
            TarotProduct.objects.select_related('mazo', 'mazo__set'),
            pk=pk
        )
        
        # Verificar que el mazo existe
        if not hasattr(producto, 'mazo') or not producto.mazo:
            messages.error(request, 'Este producto tiene un mazo inválido.')
            return redirect('tienda:admin_producto_list')
        
        context = {
            'producto': producto,
            'title': f'Producto: {producto.mazo.nombre}',
            'cartas_muestra': producto.get_primeras_cartas(3),
        }
        return render(request, 'tienda/admin/producto_detail.html', context)
        
    except Exception as e:
        print(f"Error en admin_producto_detail: {e}")
        messages.error(request, f'Error al cargar el producto: {str(e)}')
        return redirect('tienda:admin_producto_list')

@user_passes_test(is_staff_user)
def admin_producto_update(request, pk):
    """
    Actualizar producto existente - CON VALIDACIÓN
    """
    try:
        producto = get_object_or_404(TarotProduct, pk=pk)
        
        if request.method == 'POST':
            form = TarotProductForm(request.POST, instance=producto)
            if form.is_valid():
                try:
                    producto = form.save()
                    messages.success(request, f'Producto "{producto.mazo.nombre}" actualizado exitosamente.')
                    return redirect('tienda:admin_producto_detail', pk=producto.pk)
                except Exception as e:
                    print(f"Error al actualizar producto: {e}")
                    messages.error(request, f'Error al actualizar el producto: {str(e)}')
            else:
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
        
    except Exception as e:
        print(f"Error en admin_producto_update: {e}")
        messages.error(request, f'Error al editar el producto: {str(e)}')
        return redirect('tienda:admin_producto_list')

@user_passes_test(is_staff_user)
def admin_producto_delete(request, pk):
    """
    Eliminar producto - CON VALIDACIÓN
    """
    try:
        producto = get_object_or_404(TarotProduct, pk=pk)
        
        if request.method == 'POST':
            nombre = producto.nombre_mazo  # Usar propiedad segura
            try:
                producto.delete()
                messages.success(request, f'Producto "{nombre}" eliminado exitosamente.')
                return redirect('tienda:admin_producto_list')
            except Exception as e:
                print(f"Error al eliminar producto: {e}")
                messages.error(request, f'Error al eliminar el producto: {str(e)}')
                return redirect('tienda:admin_producto_detail', pk=producto.pk)
        
        context = {
            'producto': producto,
            'title': f'Eliminar: {producto.nombre_mazo}'
        }
        return render(request, 'tienda/admin/producto_confirm_delete.html', context)
        
    except Exception as e:
        print(f"Error en admin_producto_delete: {e}")
        messages.error(request, f'Error al procesar eliminación: {str(e)}')
        return redirect('tienda:admin_producto_list')
    

# ============== VISTAS DE COMPRAS PARA CLIENTES ============== #

@login_required
def mis_compras(request):
    """
    Vista para que el usuario vea sus productos comprados
    """
    try:
        compras = CompraProducto.objects.filter(
            usuario=request.user
        ).select_related('producto', 'producto__mazo', 'producto__mazo__set').order_by('-fecha_compra')
        
        # Filtros básicos
        estado_filter = request.GET.get('estado')
        if estado_filter:
            compras = compras.filter(estado=estado_filter)
        
        # Búsqueda simple
        search = request.GET.get('search')
        if search:
            compras = compras.filter(
                Q(producto__mazo__nombre__icontains=search) |
                Q(producto__mazo__set__nombre__icontains=search)
            )
        
        # Paginación
        paginator = Paginator(compras, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas básicas
        stats = {
            'total_compras': compras.count(),
            'completadas': compras.filter(estado='completada').count(),
            'pendientes': compras.filter(estado='pendiente').count(),
        }
        
        context = {
            'title': 'Mis Compras',
            'page_obj': page_obj,
            'stats': stats,
            'estado_filter': estado_filter,
            'search': search,
            'estados': CompraProducto.ESTADO_COMPRA_CHOICES,
        }
        
        return render(request, 'tienda/mis_compras.html', context)
        
    except Exception as e:
        print(f"Error en mis_compras: {e}")
        messages.error(request, 'Error al cargar tus compras.')
        return redirect('tienda:home')

@login_required
def detalle_compra(request, compra_id):
    """
    Detalle de una compra específica del usuario
    """
    try:
        compra = get_object_or_404(
            CompraProducto.objects.select_related('producto', 'producto__mazo', 'producto__mazo__set'),
            id=compra_id,
            usuario=request.user
        )
        
        # Cartas del producto (solo si la compra está completada)
        cartas_producto = []
        if compra.puede_descargar:
            cartas_producto = compra.producto.mazo.cartas.all().order_by('numero')
        
        context = {
            'title': f'Compra: {compra.producto.mazo.nombre}',
            'compra': compra,
            'cartas_producto': cartas_producto,
        }
        
        return render(request, 'tienda/detalle_compra.html', context)
        
    except Exception as e:
        print(f"Error en detalle_compra: {e}")
        messages.error(request, 'Error al cargar el detalle de la compra.')
        return redirect('tienda:mis_compras')