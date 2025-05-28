from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from .models import Set, Mazo, Carta
from .forms import SetForm, MazoForm, CartaForm, BuscarCartasForm

# ============== DASHBOARD ============== #

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