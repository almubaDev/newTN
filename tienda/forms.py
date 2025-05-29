from django import forms
from .models import TarotProduct
from oraculo.models import Mazo

class TarotProductForm(forms.ModelForm):
    """
    Formulario para crear y editar productos de tarot - VERSIÓN DEBUG
    """
    mazo = forms.ModelChoiceField(
        queryset=Mazo.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
        }),
        empty_label="Selecciona un Mazo"
    )
    
    precio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        })
    )
    
    precio_oferta = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-green-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 transition-colors',
            'placeholder': '0.00 (opcional)',
            'step': '0.01',
            'min': '0.01'
        })
    )
    
    link_compra = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'https://...'
        })
    )
    
    descripcion_adicional = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-cosmic-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-cosmic-400 focus:ring-1 focus:ring-cosmic-400 transition-colors',
            'placeholder': 'Descripción adicional del producto (opcional)...',
            'rows': 4
        })
    )
    
    estado = forms.ChoiceField(
        choices=TarotProduct.ESTADO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
        })
    )
    
    orden = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
            'placeholder': '0',
            'min': '0'
        })
    )
    
    destacado = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-cosmic-300 rounded'
        })
    )
    
    class Meta:
        model = TarotProduct
        fields = [
            'mazo', 'precio', 'precio_oferta', 'link_compra', 
            'descripcion_adicional', 'estado', 'destacado', 'orden'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        
        # DEBUG: Imprimir información de inicialización
        print(f"Inicializando formulario TarotProduct")
        print(f"Instance: {self.instance}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        
        # Filtrar solo mazos que no tienen producto asociado (en creación)
        if not self.instance.pk:
            try:
                mazos_sin_producto = Mazo.objects.filter(producto__isnull=True)
                print(f"Mazos sin producto encontrados: {mazos_sin_producto.count()}")
                self.fields['mazo'].queryset = mazos_sin_producto
            except Exception as e:
                print(f"Error filtrando mazos: {e}")
                # Si hay error, usar todos los mazos
                self.fields['mazo'].queryset = Mazo.objects.all()
        
        # Mejorar la visualización de mazos en el select
        try:
            self.fields['mazo'].queryset = self.fields['mazo'].queryset.select_related('set')
            self.fields['mazo'].label_from_instance = lambda obj: f"{obj.nombre} ({obj.set.nombre})"
        except Exception as e:
            print(f"Error configurando queryset de mazos: {e}")
    
    def clean_precio_oferta(self):
        """Validación simplificada del precio de oferta"""
        precio_oferta = self.cleaned_data.get('precio_oferta')
        precio = self.cleaned_data.get('precio')
        
        if precio_oferta and precio and precio_oferta >= precio:
            raise forms.ValidationError('El precio de oferta debe ser menor al precio normal.')
        
        return precio_oferta
    
    def clean_mazo(self):
        """Validación del mazo"""
        mazo = self.cleaned_data.get('mazo')
        
        if not mazo:
            raise forms.ValidationError('Debes seleccionar un mazo.')
        
        # Verificar que el mazo no tenga ya un producto asociado (solo en creación)
        if not self.instance.pk:
            try:
                if hasattr(mazo, 'producto'):
                    raise forms.ValidationError(f'El mazo "{mazo.nombre}" ya tiene un producto asociado.')
            except TarotProduct.DoesNotExist:
                # Esto está bien, el mazo no tiene producto
                pass
        
        return mazo
    
    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        
        # DEBUG: Imprimir datos limpios
        print(f"Datos del formulario después de clean(): {cleaned_data}")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override del método save para debugging"""
        print(f"Guardando producto, commit={commit}")
        print(f"Datos a guardar: {self.cleaned_data}")
        
        try:
            instance = super().save(commit=commit)
            print(f"Producto guardado exitosamente: {instance}")
            return instance
        except Exception as e:
            print(f"Error en save(): {e}")
            raise