from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from django.db import models
from user.models import CustomUser
from .models import Set, Mazo, Carta, ComplementosMazo
from .forms import SetForm, MazoForm, CartaForm, BuscarCartasForm, ComplementosMazoForm
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
import math
from django.core.files.base import ContentFile
import os







@staff_member_required
def generar_plantilla_pdf(request, mazo_id):
    mazo = get_object_or_404(Mazo, id=mazo_id)
    cartas = mazo.cartas.all().order_by('numero', 'id')
    
    # Organizar cartas en grupos de 4
    grupos_cartas = []
    for i in range(0, cartas.count(), 4):
        grupo = list(cartas[i:i+4])
        while len(grupo) < 4:
            grupo.append(None)
        grupos_cartas.append(grupo)
    
    # Crear grupos de reversos en orden correcto para voltear papel
    grupos_reversos = []
    for grupo in grupos_cartas:
        # Para cada grupo de anversos, crear grupo de reversos en orden inverso
        # Anversos: [1, 2, 3, 4] -> Reversos: [2, 1, 4, 3] (para coincidir al voltear)
        reverso_grupo = [grupo[1], grupo[0], grupo[3], grupo[2]] if len(grupo) >= 4 else grupo
        grupos_reversos.append(reverso_grupo)
    
    # Renderizar HTML
    html_content = render_to_string('oraculo/plantilla_pdf.html', {
        'mazo': mazo,
        'grupos_cartas': grupos_cartas,
        'grupos_reversos': grupos_reversos,
    })
    
    # Configurar base URL para imágenes
    base_url = request.build_absolute_uri('/')[:-1]
    
    # Generar PDF con base URL
    html_doc = HTML(string=html_content, base_url=base_url)
    pdf_buffer = html_doc.write_pdf()
    
    # Guardar PDF en ComplementosMazo
    complemento, created = ComplementosMazo.objects.get_or_create(mazo=mazo)
    
    # Crear nombre único para el archivo
    nombre_archivo = f'plantilla_{mazo.nombre.replace(" ", "_")}.pdf'
    
    # Guardar/actualizar el PDF en el campo plantilla_impresion
    complemento.plantilla_impresion.save(
        nombre_archivo,
        ContentFile(pdf_buffer),
        save=True
    )
    
    # Preparar respuesta para descarga
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    return response

# ============== HELPER FUNCTIONS ============== #

def is_staff_user(user):
    """Helper function to check if user is staff"""
    return user.is_authenticated and user.is_staff

# ============== DASHBOARD VIEWS ============== #

# ============== DASHBOARDs ============== #
@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """
    Dashboard administrativo para gestionar contenido
    """
    # Estadísticas generales
    total_sets = Set.objects.count()
    total_mazos = Mazo.objects.count()
    total_cartas = Carta.objects.count()
    total_usuarios = CustomUser.objects.count()
    
    # Últimos elementos creados
    ultimos_sets = Set.objects.all().order_by('-fecha_creacion')[:5]
    ultimos_mazos = Mazo.objects.select_related('set').order_by('-fecha_creacion')[:5]
    ultimas_cartas = Carta.objects.select_related('mazo', 'mazo__set').order_by('-fecha_creacion')[:5]
    
    # Sets con más mazos
    sets_populares = Set.objects.annotate(
        num_mazos=models.Count('mazos')
    ).order_by('-num_mazos')[:5]
    
    # Mazos con más cartas
    mazos_completos = Mazo.objects.annotate(
        num_cartas=models.Count('cartas')
    ).order_by('-num_cartas')[:5]
    
    context = {
        'title': 'Dashboard Administrativo',
        # Estadísticas
        'total_sets': total_sets,
        'total_mazos': total_mazos,
        'total_cartas': total_cartas,
        'total_usuarios': total_usuarios,
        # Últimos elementos
        'ultimos_sets': ultimos_sets,
        'ultimos_mazos': ultimos_mazos,
        'ultimas_cartas': ultimas_cartas,
        # Populares
        'sets_populares': sets_populares,
        'mazos_completos': mazos_completos,
    }
    
    return render(request, 'oraculo/admin_dashboard.html', context)


def dashboard(request):
    """
    Vista principal del dashboard de Tarotnaútica
    """
    context = {
        'page_title': 'Dashboard - Tarotnaútica',
        'app_name': 'Tarotnaútica',
        'tagline': 'Navegando el cosmos interior'
    }
    
    return render(request, 'oraculo/dashboard.html', context)

def motor_nautica(request):
    """
    Vista de la página del Motor Náutica
    """
    context = {
        'page_title': 'Motor Náutica - Tarotnaútica',
        'app_name': 'Tarotnaútica',
        'section': 'Motor Náutica'
    }
    
    return render(request, 'oraculo/motornautica.html', context)

# ============== HELPER FUNCTIONS ============== #

def is_staff_user(user):
    """Helper function to check if user is staff"""
    return user.is_authenticated and user.is_staff

# ============== SET VIEWS ============== #

@login_required
@user_passes_test(is_staff_user)
def set_list(request):
    """
    Lista todos los sets con paginación y búsqueda
    """
    sets = Set.objects.all().order_by('-fecha_creacion')
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        sets = sets.filter(
            Q(nombre__icontains=search) | 
            Q(codigo__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(sets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'title': 'Gestión de Sets'
    }
    return render(request, 'oraculo/set_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def set_detail(request, pk):
    """
    Detalle de un set específico
    """
    set_obj = get_object_or_404(Set, pk=pk)
    mazos = set_obj.mazos.all().order_by('nombre')
    
    context = {
        'set': set_obj,
        'mazos': mazos,
        'title': f'Set: {set_obj.nombre}'
    }
    return render(request, 'oraculo/set_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def set_create(request):
    """
    Crear un nuevo set
    """
    if request.method == 'POST':
        form = SetForm(request.POST)
        if form.is_valid():
            set_obj = form.save()
            messages.success(request, f'Set "{set_obj.nombre}" creado exitosamente.')
            return redirect('oraculo:set_detail', pk=set_obj.pk)
    else:
        form = SetForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Set',
        'action': 'Crear'
    }
    return render(request, 'oraculo/set_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def set_update(request, pk):
    """
    Actualizar un set existente
    """
    set_obj = get_object_or_404(Set, pk=pk)
    
    if request.method == 'POST':
        form = SetForm(request.POST, instance=set_obj)
        if form.is_valid():
            set_obj = form.save()
            messages.success(request, f'Set "{set_obj.nombre}" actualizado exitosamente.')
            return redirect('oraculo:set_detail', pk=set_obj.pk)
    else:
        form = SetForm(instance=set_obj)
    
    context = {
        'form': form,
        'set': set_obj,
        'title': f'Editar Set: {set_obj.nombre}',
        'action': 'Actualizar'
    }
    return render(request, 'oraculo/set_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def set_delete(request, pk):
    """
    Eliminar un set
    """
    set_obj = get_object_or_404(Set, pk=pk)
    
    if request.method == 'POST':
        nombre = set_obj.nombre
        set_obj.delete()
        messages.success(request, f'Set "{nombre}" eliminado exitosamente.')
        return redirect('oraculo:set_list')
    
    context = {
        'set': set_obj,
        'title': f'Eliminar Set: {set_obj.nombre}'
    }
    return render(request, 'oraculo/set_confirm_delete.html', context)

# ============== MAZO VIEWS ============== #

@login_required
@user_passes_test(is_staff_user)
def mazo_list(request):
    """
    Lista todos los mazos con paginación y búsqueda
    """
    mazos = Mazo.objects.select_related('set').all().order_by('-fecha_creacion')
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        mazos = mazos.filter(
            Q(nombre__icontains=search) | 
            Q(codigo__icontains=search) |
            Q(descripcion__icontains=search) |
            Q(set__nombre__icontains=search)
        )
    
    # Filtro por set
    set_filter = request.GET.get('set')
    if set_filter:
        mazos = mazos.filter(set_id=set_filter)
    
    # Paginación
    paginator = Paginator(mazos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'sets': Set.objects.all(),
        'set_filter': set_filter,
        'title': 'Gestión de Mazos'
    }
    return render(request, 'oraculo/mazo_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def mazo_detail(request, pk):
    """
    Detalle de un mazo específico
    """
    mazo = get_object_or_404(Mazo, pk=pk)
    cartas = mazo.cartas.all().order_by('numero')
    
    context = {
        'mazo': mazo,
        'cartas': cartas,
        'title': f'Mazo: {mazo.nombre}'
    }
    return render(request, 'oraculo/mazo_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def mazo_create(request):
    """
    Crear un nuevo mazo
    """
    if request.method == 'POST':
        form = MazoForm(request.POST, request.FILES)
        if form.is_valid():
            mazo = form.save()
            messages.success(request, f'Mazo "{mazo.nombre}" creado exitosamente.')
            return redirect('oraculo:mazo_detail', pk=mazo.pk)
    else:
        form = MazoForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Mazo',
        'action': 'Crear'
    }
    return render(request, 'oraculo/mazo_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def mazo_update(request, pk):
    """
    Actualizar un mazo existente
    """
    mazo = get_object_or_404(Mazo, pk=pk)
    
    if request.method == 'POST':
        form = MazoForm(request.POST, request.FILES, instance=mazo)
        if form.is_valid():
            mazo = form.save()
            messages.success(request, f'Mazo "{mazo.nombre}" actualizado exitosamente.')
            return redirect('oraculo:mazo_detail', pk=mazo.pk)
    else:
        form = MazoForm(instance=mazo)
    
    context = {
        'form': form,
        'mazo': mazo,
        'title': f'Editar Mazo: {mazo.nombre}',
        'action': 'Actualizar'
    }
    return render(request, 'oraculo/mazo_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def mazo_delete(request, pk):
    """
    Eliminar un mazo
    """
    mazo = get_object_or_404(Mazo, pk=pk)
    
    if request.method == 'POST':
        nombre = mazo.nombre
        mazo.delete()
        messages.success(request, f'Mazo "{nombre}" eliminado exitosamente.')
        return redirect('oraculo:mazo_list')
    
    context = {
        'mazo': mazo,
        'title': f'Eliminar Mazo: {mazo.nombre}'
    }
    return render(request, 'oraculo/mazo_confirm_delete.html', context)

# ============== CARTA VIEWS ============== #
@login_required
@user_passes_test(is_staff_user)
def carta_list(request):
    """
    Lista todas las cartas (público con búsqueda)
    """
    cartas = Carta.objects.select_related('mazo', 'mazo__set').all().order_by('mazo__nombre', 'numero')
    
    # Formulario de búsqueda
    form = BuscarCartasForm(request.GET)
    
    if form.is_valid():
        busqueda = form.cleaned_data.get('busqueda')
        set_filtro = form.cleaned_data.get('set')
        mazo_filtro = form.cleaned_data.get('mazo')
        
        if busqueda:
            cartas = cartas.filter(
                Q(nombre__icontains=busqueda) |
                Q(mazo__nombre__icontains=busqueda) |
                Q(mazo__set__nombre__icontains=busqueda) |
                Q(significado_normal__icontains=busqueda) |
                Q(significado_invertido__icontains=busqueda)
            )
        
        if set_filtro:
            cartas = cartas.filter(mazo__set=set_filtro)
        
        if mazo_filtro:
            cartas = cartas.filter(mazo=mazo_filtro)
    
    # Paginación
    paginator = Paginator(cartas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'title': 'Catálogo de Cartas'
    }
    return render(request, 'oraculo/carta_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def carta_detail(request, pk):
    """
    Detalle de una carta específica (público)
    """
    carta = get_object_or_404(Carta, pk=pk)
    
    context = {
        'carta': carta,
        'title': f'Carta: {carta.nombre}'
    }
    return render(request, 'oraculo/carta_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def carta_create(request):
    """
    Crear una nueva carta
    """
    if request.method == 'POST':
        form = CartaForm(request.POST, request.FILES)
        if form.is_valid():
            carta = form.save()
            messages.success(request, f'Carta "{carta.nombre}" creada exitosamente.')
            return redirect('oraculo:carta_detail', pk=carta.pk)
    else:
        form = CartaForm()
        # Pre-seleccionar mazo si viene en la URL
        mazo_id = request.GET.get('mazo')
        if mazo_id:
            try:
                mazo = Mazo.objects.get(pk=mazo_id)
                form.fields['mazo'].initial = mazo
            except Mazo.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'title': 'Crear Nueva Carta',
        'action': 'Crear'
    }
    return render(request, 'oraculo/carta_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def carta_update(request, pk):
    """
    Actualizar una carta existente
    """
    carta = get_object_or_404(Carta, pk=pk)
    
    if request.method == 'POST':
        form = CartaForm(request.POST, request.FILES, instance=carta)
        if form.is_valid():
            carta = form.save()
            messages.success(request, f'Carta "{carta.nombre}" actualizada exitosamente.')
            return redirect('oraculo:carta_detail', pk=carta.pk)
    else:
        form = CartaForm(instance=carta)
    
    context = {
        'form': form,
        'carta': carta,
        'title': f'Editar Carta: {carta.nombre}',
        'action': 'Actualizar'
    }
    return render(request, 'oraculo/carta_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def carta_delete(request, pk):
    """
    Eliminar una carta
    """
    carta = get_object_or_404(Carta, pk=pk)
    
    if request.method == 'POST':
        nombre = carta.nombre
        mazo = carta.mazo
        carta.delete()
        messages.success(request, f'Carta "{nombre}" eliminada exitosamente.')
        return redirect('oraculo:mazo_detail', pk=mazo.pk)
    
    context = {
        'carta': carta,
        'title': f'Eliminar Carta: {carta.nombre}'
    }
    return render(request, 'oraculo/carta_confirm_delete.html', context)

# ============== AJAX VIEWS ============== #

@login_required
@user_passes_test(is_staff_user)
def get_mazos_by_set(request):
    """
    Vista AJAX para obtener mazos por set
    """
    set_id = request.GET.get('set_id')
    mazos = Mazo.objects.filter(set_id=set_id).values('id', 'nombre')
    return JsonResponse({'mazos': list(mazos)})



# ============== VISTAS PARA COMPLEMENTOS DE MAZO ============== #

@login_required
@user_passes_test(is_staff_user)
def complementos_mazo_manage(request, mazo_pk):
    """
    Gestionar complementos de un mazo específico
    """
    mazo = get_object_or_404(Mazo, pk=mazo_pk)
    
    # Obtener o crear complementos
    complementos, created = ComplementosMazo.objects.get_or_create(mazo=mazo)
    
    if request.method == 'POST':
        form = ComplementosMazoForm(request.POST, request.FILES, instance=complementos)
        if form.is_valid():
            try:
                complementos = form.save()
                messages.success(request, f'Complementos del mazo "{mazo.nombre}" actualizados exitosamente.')
                return redirect('oraculo:mazo_detail', pk=mazo.pk)
            except Exception as e:
                print(f"Error al guardar complementos: {e}")
                messages.error(request, f'Error al actualizar complementos: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ComplementosMazoForm(instance=complementos)
    
    context = {
        'form': form,
        'mazo': mazo,
        'complementos': complementos,
        'title': f'Complementos: {mazo.nombre}',
        'action': 'Actualizar' if not created else 'Configurar'
    }
    return render(request, 'oraculo/complementos_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def complementos_download(request, mazo_pk, tipo):
    """
    Descargar archivos de complementos
    """
    mazo = get_object_or_404(Mazo, pk=mazo_pk)
    
    try:
        complementos = mazo.complementos
        
        if tipo == 'instructivo' and complementos.tiene_instructivo():
            response = HttpResponse(
                complementos.instructivo.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{complementos.instructivo.name}"'
            return response
        
        elif tipo == 'plantilla' and complementos.tiene_plantilla():
            response = HttpResponse(
                complementos.plantilla_impresion.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{complementos.plantilla_impresion.name}"'
            return response
        
        else:
            messages.error(request, 'Archivo no encontrado o no disponible.')
            
    except ComplementosMazo.DoesNotExist:
        messages.error(request, 'Este mazo no tiene complementos configurados.')
    except Exception as e:
        print(f"Error en descarga de complementos: {e}")
        messages.error(request, 'Error al acceder al archivo.')
    
    return redirect('oraculo:mazo_detail', pk=mazo_pk)

@login_required
@user_passes_test(is_staff_user)
def complementos_delete_file(request, mazo_pk, tipo):
    """
    Eliminar un archivo específico de complementos
    """
    mazo = get_object_or_404(Mazo, pk=mazo_pk)
    
    try:
        complementos = mazo.complementos
        
        if tipo == 'instructivo' and complementos.tiene_instructivo():
            # Eliminar archivo físico
            complementos.instructivo.delete()
            # Limpiar campo en BD
            complementos.instructivo = None
            complementos.save()
            messages.success(request, 'Instructivo eliminado exitosamente.')
            
        elif tipo == 'plantilla' and complementos.tiene_plantilla():
            # Eliminar archivo físico
            complementos.plantilla_impresion.delete()
            # Limpiar campo en BD
            complementos.plantilla_impresion = None
            complementos.save()
            messages.success(request, 'Plantilla eliminada exitosamente.')
            
        else:
            messages.warning(request, 'No hay archivo para eliminar.')
            
    except ComplementosMazo.DoesNotExist:
        messages.error(request, 'Este mazo no tiene complementos configurados.')
    except Exception as e:
        print(f"Error al eliminar archivo de complementos: {e}")
        messages.error(request, f'Error al eliminar archivo: {str(e)}')
    
    return redirect('oraculo:complementos_mazo_manage', mazo_pk=mazo_pk)