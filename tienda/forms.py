from django import forms
from .models import TarotProduct
from oraculo.models import Mazo

class TarotProductForm(forms.ModelForm):
    """
    Formulario para crear y editar productos de tarot - CORREGIDO
    """
    
    class Meta:
        model = TarotProduct
        fields = [
            'mazo', 'precio', 'precio_oferta', 'link_compra', 
            'descripcion_adicional', 'estado', 'destacado', 'orden'
        ]
        widgets = {
            'mazo': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'precio_oferta': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-green-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 transition-colors',
                'placeholder': '0.00 (opcional)',
                'step': '0.01',
                'min': '0.01'
            }),
            'link_compra': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-primary-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 transition-colors',
                'placeholder': 'https://...'
            }),
            'descripcion_adicional': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-cosmic-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-cosmic-400 focus:ring-1 focus:ring-cosmic-400 transition-colors',
                'placeholder': 'Descripción adicional del producto (opcional)...',
                'rows': 4
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-mystic-500/30 text-cosmic-100 focus:outline-none focus:border-mystic-400 focus:ring-1 focus:ring-mystic-400 transition-colors'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-cosmic-700/50 border border-gold-500/30 text-cosmic-100 placeholder-cosmic-400 focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400 transition-colors',
                'placeholder': '0',
                'min': '0'
            }),
            'destacado': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-cosmic-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        print(f"🔧 INICIALIZANDO FORMULARIO CORREGIDO")
        print(f"   Args: {len(args)} argumentos")
        print(f"   Kwargs: {kwargs.keys()}")
        
        # CRÍTICO: Llamar a super() ANTES de configurar campos
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de mazos DESPUÉS de super()
        try:
            if not self.instance.pk:
                # Solo mazos sin producto para creación
                mazos_disponibles = Mazo.objects.filter(producto__isnull=True).select_related('set')
                print(f"   📋 Mazos sin producto: {mazos_disponibles.count()}")
            else:
                # Todos los mazos para edición (incluir el actual)
                mazos_disponibles = Mazo.objects.all().select_related('set')
                print(f"   📋 Todos los mazos: {mazos_disponibles.count()}")
            
            self.fields['mazo'].queryset = mazos_disponibles
            self.fields['mazo'].empty_label = "Selecciona un Mazo"
            
            # Hacer campos opcionales explícitamente
            self.fields['precio_oferta'].required = False
            self.fields['descripcion_adicional'].required = False
            self.fields['destacado'].required = False
            
            print(f"   ✅ Configuración completada correctamente")
            
        except Exception as e:
            print(f"   ❌ Error configurando formulario: {e}")
            import traceback
            traceback.print_exc()
            # Fallback seguro
            self.fields['mazo'].queryset = Mazo.objects.all()
    
    def clean_precio_oferta(self):
        """Validar precio de oferta"""
        print(f"🔍 VALIDANDO precio_oferta")
        precio_oferta = self.cleaned_data.get('precio_oferta')
        precio = self.cleaned_data.get('precio')
        
        print(f"   - precio_oferta: {precio_oferta}")
        print(f"   - precio: {precio}")
        
        if precio_oferta and precio and precio_oferta >= precio:
            print(f"   ❌ Error: precio_oferta >= precio")
            raise forms.ValidationError('El precio de oferta debe ser menor al precio normal.')
        
        print(f"   ✅ precio_oferta válido")
        return precio_oferta
    
    def clean_mazo(self):
        """Validar que el mazo existe y no tiene producto"""
        print(f"🔍 VALIDANDO mazo")
        mazo = self.cleaned_data.get('mazo')
        
        print(f"   - mazo seleccionado: {mazo}")
        
        if not mazo:
            print(f"   ❌ Error: No hay mazo seleccionado")
            raise forms.ValidationError('Debes seleccionar un mazo.')
        
        # Solo verificar duplicados en creación
        if not self.instance.pk:
            try:
                existe_producto = TarotProduct.objects.filter(mazo=mazo).exists()
                print(f"   - ¿Mazo ya tiene producto? {existe_producto}")
                
                if existe_producto:
                    print(f"   ❌ Error: Mazo ya tiene producto")
                    raise forms.ValidationError(f'El mazo "{mazo.nombre}" ya tiene un producto asociado.')
            except Exception as e:
                print(f"   ⚠️  Error verificando duplicados: {e}")
        
        print(f"   ✅ mazo válido: {mazo}")
        return mazo
    
    def clean(self):
        """Validación general del formulario"""
        print(f"🔍 VALIDACIÓN GENERAL DEL FORMULARIO")
        
        try:
            cleaned_data = super().clean()
            print(f"   ✅ super().clean() ejecutado")
            print(f"   📋 Datos limpios: {list(cleaned_data.keys()) if cleaned_data else 'None'}")
            return cleaned_data
        except Exception as e:
            print(f"   ❌ Error en clean(): {e}")
            import traceback
            traceback.print_exc()
            raise