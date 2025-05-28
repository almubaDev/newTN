from django import forms
from .models import Set, Mazo, Carta

class SetForm(forms.ModelForm):
    """
    Formulario para crear y editar Sets de cartas
    """
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Nombre del Set (ej: Jardín del Corazón)'
        })
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Descripción detallada del set...',
            'rows': 4
        })
    )
    codigo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
            'placeholder': 'Código único (ej: JDC2024)'
        })
    )
    
    class Meta:
        model = Set
        fields = ['nombre', 'descripcion', 'codigo']
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            # Verificar unicidad solo si es un nuevo registro o el código cambió
            if self.instance.pk:
                if Set.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Este código ya existe.')
            else:
                if Set.objects.filter(codigo=codigo).exists():
                    raise forms.ValidationError('Este código ya existe.')
        return codigo


class MazoForm(forms.ModelForm):
    """
    Formulario para crear y editar Mazos de cartas
    """
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Nombre del Mazo'
        })
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Descripción del mazo...',
            'rows': 4
        })
    )
    codigo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
            'placeholder': 'Código único del mazo'
        })
    )
    set = forms.ModelChoiceField(
        queryset=Set.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
        }),
        empty_label="Selecciona un Set"
    )
    imagen_reverso = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-500 file:text-white hover:file:bg-primary-600 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = Mazo
        fields = ['nombre', 'descripcion', 'codigo', 'imagen_reverso', 'set']
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            # Verificar unicidad
            if self.instance.pk:
                if Mazo.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Este código ya existe.')
            else:
                if Mazo.objects.filter(codigo=codigo).exists():
                    raise forms.ValidationError('Este código ya existe.')
        return codigo


class CartaForm(forms.ModelForm):
    """
    Formulario para crear y editar Cartas individuales
    """
    numero = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
            'placeholder': 'Número de la carta (ej: 1)'
        })
    )
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Nombre de la carta'
        })
    )
    imagen = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-500 file:text-white hover:file:bg-primary-600 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'accept': 'image/*'
        })
    )
    significado_normal = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-green-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 transition-colors',
            'placeholder': 'Significado cuando la carta aparece en posición normal...',
            'rows': 5
        })
    )
    significado_invertido = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-red-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400 transition-colors',
            'placeholder': 'Significado cuando la carta aparece invertida...',
            'rows': 5
        })
    )
    mazo = forms.ModelChoiceField(
        queryset=Mazo.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
        }),
        empty_label="Selecciona un Mazo"
    )
    
    class Meta:
        model = Carta
        fields = ['numero', 'nombre', 'imagen', 'significado_normal', 'significado_invertido', 'mazo']
    
    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        mazo = cleaned_data.get('mazo')
        
        if numero and mazo:
            # Verificar que no exista otra carta con el mismo número en el mismo mazo
            if self.instance.pk:
                if Carta.objects.filter(numero=numero, mazo=mazo).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(f'Ya existe una carta con el número {numero} en este mazo.')
            else:
                if Carta.objects.filter(numero=numero, mazo=mazo).exists():
                    raise forms.ValidationError(f'Ya existe una carta con el número {numero} en este mazo.')
        
        return cleaned_data


class BuscarCartasForm(forms.Form):
    """
    Formulario para buscar cartas
    """
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
            'placeholder': 'Buscar por nombre de carta, mazo o set...'
        })
    )
    set = forms.ModelChoiceField(
        queryset=Set.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
        }),
        empty_label="Todos los Sets"
    )
    mazo = forms.ModelChoiceField(
        queryset=Mazo.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors'
        }),
        empty_label="Todos los Mazos"
    )