from django import forms
from .models import TarotProduct
from oraculo.models import Mazo

class TarotProductForm(forms.ModelForm):
    """
    Formulario para crear y editar productos de tarot
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
    
    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get('precio')
        precio_oferta = cleaned_data.get('precio_oferta')
        mazo = cleaned_data.get('mazo')
        
        # Validar que el precio de oferta sea menor al precio normal
        if precio_oferta and precio and precio_oferta >= precio:
            raise forms.ValidationError(
                'El precio de oferta debe ser menor al precio normal.'
            )
        
        # Validar que el mazo no tenga ya un producto asociado (solo en creación)
        if mazo and not self.instance.pk:
            if hasattr(mazo, 'producto'):
                raise forms.ValidationError(
                    f'El mazo "{mazo.nombre}" ya tiene un producto asociado.'
                )
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        
        # Filtrar solo mazos que no tienen producto asociado (en creación)
        if not self.instance.pk:
            mazos_sin_producto = Mazo.objects.filter(producto__isnull=True)
            self.fields['mazo'].queryset = mazos_sin_producto
        
        # Mejorar la visualización de mazos en el select
        self.fields['mazo'].queryset = self.fields['mazo'].queryset.select_related('set')
        self.fields['mazo'].label_from_instance = lambda obj: f"{obj.nombre} ({obj.set.nombre})"