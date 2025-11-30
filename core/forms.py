from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Producto, Repartidor, Reclamo, Resena
from django.core.exceptions import ValidationError
import re

# Clases de Tailwind CSS para inputs
TAILWIND_INPUT_CLASSES = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_TEXTAREA_CLASSES = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_SELECT_CLASSES = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_CHECKBOX_CLASSES = 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'

class RegistroForm(UserCreationForm):
    """Formulario de registro con código de país (solo Chile)"""
    
    email = forms.EmailField(
        required=True,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'tucorreo@ejemplo.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Nombres',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu apellido'
        })
    )
    
    # ✅ CAMPO DE TELÉFONO OBLIGATORIO (SOLO CHILE +56)
    codigo_pais = forms.ChoiceField(
        choices=[
            ('+56', '🇨🇱 +56 (Chile)'),
        ],
        initial='+56',
        required=True,
        label='Código País',
        widget=forms.Select(attrs={
            'class': 'px-3 py-3 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-primary focus:border-transparent transition bg-gray-50'
        })
    )
    
    telefono = forms.CharField(
        max_length=15, 
        required=True,  # ✅ AHORA ES OBLIGATORIO
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'flex-1 px-4 py-3 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
            'placeholder': '9 1234 5678',
            'pattern': '[0-9]{9}',
            'title': 'Ingresa 9 dígitos (ejemplo: 912345678)'
        }),
        error_messages={
            'required': 'El teléfono es obligatorio.'
        }
    )
    
    direccion = forms.CharField(
        required=False, 
        label='Dirección',
        widget=forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA_CLASSES,
            'rows': 3,
            'placeholder': 'Ingresa tu dirección (opcional)'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'codigo_pais', 'telefono', 'direccion', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES, 
                'placeholder': 'Nombre de usuario'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Confirmar contraseña'
        })
        
        self.fields['password1'].help_text = 'Mínimo 8 caracteres, debe contener una mayúscula y un número'
    
    def clean_email(self):
        """Validar que el email no esté registrado"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_telefono(self):
        """Validar formato del teléfono chileno"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        # ✅ Validación estricta
        if not telefono:
            raise ValidationError('El teléfono es obligatorio.')
        
        # Eliminar espacios y guiones
        telefono_limpio = telefono.replace(' ', '').replace('-', '')
        
        # Validar que sean solo números
        if not telefono_limpio.isdigit():
            raise ValidationError('El teléfono debe contener solo números.')
        
        # Validar longitud exacta (9 dígitos para Chile)
        if len(telefono_limpio) != 9:
            raise ValidationError('El teléfono debe tener exactamente 9 dígitos.')
        
        # Validar que empiece con 9 (celulares chilenos)
        if not telefono_limpio.startswith('9'):
            raise ValidationError('El número de celular debe comenzar con 9.')
        
        return telefono
    
    def clean_password1(self):
        """Validar requisitos de contraseña"""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        return password
    
    def save(self, commit=True):
        """Guardar usuario con teléfono completo (código + número)"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.rol = 'cliente'
        
        # Combinar código de país con teléfono
        codigo = self.cleaned_data.get('codigo_pais', '+56')
        telefono = self.cleaned_data.get('telefono', '').strip()
        user.telefono = f"{codigo} {telefono}"
        
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Nombre de usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Contraseña'
        })
    )


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion']
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'telefono': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'direccion': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA_CLASSES, 'rows': 3})
        }


class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'tucorreo@ejemplo.com'
        }),
        help_text='Ingresa el correo con el que te registraste'
    )


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu nueva contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Confirma tu nueva contraseña'
        })
    )


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'sku', 'descripcion', 'precio', 'imagen', 'stock', 'categoria', 'activo', 'en_promocion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'sku': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'SKU/Código de Barras (Opcional)'}),
            'descripcion': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA_CLASSES, 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'stock': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'categoria': forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES}),
            'activo': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX_CLASSES}),
            'en_promocion': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX_CLASSES}),
        }


# ========== FORMULARIOS DE REPARTIDOR ==========

class RepartidorUserForm(forms.ModelForm):
    """Formulario para editar datos de usuario del repartidor"""
    
    # ✅ NUEVO: Campo de código de país (solo Chile)
    codigo_pais = forms.ChoiceField(
        choices=[
            ('+56', '🇨🇱 +56 (Chile)'),
        ],
        initial='+56',
        required=True,
        label='Código País',
        widget=forms.Select(attrs={
            'class': 'px-3 py-3 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-primary focus:border-transparent transition bg-gray-50',
            'style': 'width: 120px;'
        })
    )
    
    # ✅ NUEVO: Campo de teléfono separado del código
    telefono_numero = forms.CharField(
        max_length=15,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'flex-1 px-4 py-3 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
            'placeholder': '9 1234 5678',
            'pattern': '[0-9]{9}',
            'title': 'Ingresa 9 dígitos (ejemplo: 912345678)'
        }),
        error_messages={
            'required': 'El teléfono es obligatorio para repartidores.'
        }
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'nombre_de_usuario'}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'correo@ejemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ Si estamos editando, extraer código y número del teléfono existente
        if self.instance and self.instance.telefono:
            telefono_completo = self.instance.telefono.strip()
            # Intentar separar código de país del número
            partes = telefono_completo.split(' ', 1)
            if len(partes) == 2:
                self.fields['codigo_pais'].initial = partes[0]
                self.fields['telefono_numero'].initial = partes[1].replace(' ', '').replace('-', '')
            else:
                # Si no tiene formato esperado, poner todo en el número
                self.fields['telefono_numero'].initial = telefono_completo.replace('+56', '').replace(' ', '').replace('-', '')
    
    def clean_telefono_numero(self):
        """Validar formato del teléfono chileno"""
        telefono = self.cleaned_data.get('telefono_numero', '').strip()
        
        if not telefono:
            raise ValidationError('El teléfono es obligatorio para repartidores.')
        
        telefono_limpio = telefono.replace(' ', '').replace('-', '')
        
        if not telefono_limpio.isdigit():
            raise ValidationError('El teléfono debe contener solo números.')
        
        if len(telefono_limpio) != 9:
            raise ValidationError('El teléfono debe tener exactamente 9 dígitos.')
        
        if not telefono_limpio.startswith('9'):
            raise ValidationError('El número de celular debe comenzar con 9.')
        
        return telefono
    
    def save(self, commit=True):
        """Guardar usuario combinando código + número"""
        user = super().save(commit=False)
        
        # Combinar código de país con teléfono
        codigo = self.cleaned_data.get('codigo_pais', '+56')
        telefono = self.cleaned_data.get('telefono_numero', '').strip()
        user.telefono = f"{codigo} {telefono}"
        
        if commit:
            user.save()
        return user


class RepartidorProfileForm(forms.ModelForm):
    class Meta:
        model = Repartidor
        fields = ['vehiculo', 'placa_vehiculo', 'disponible']
        labels = {
            'placa_vehiculo': 'Placa Patente',
            'disponible': 'Disponible para entregas'
        }
        widgets = {
            'vehiculo': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'Ej: Moto Honda CB190R'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'placeholder': 'Ej: ABCD12'}),
            'disponible': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX_CLASSES + ' ml-2'}),
        }


class RepartidorCreateForm(UserCreationForm):
    """Formulario para CREAR un nuevo usuario Repartidor (con contraseña)"""
    
    email = forms.EmailField(
        required=True, 
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'tucorreo@ejemplo.com'
        })
    )
    
    first_name = forms.CharField(
        required=True, 
        label='Nombres',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Ingresa su nombre'
        })
    )
    
    last_name = forms.CharField(
        required=True, 
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Ingresa su apellido'
        })
    )
    
    # ✅ CAMPOS DE TELÉFONO OBLIGATORIOS (SOLO CHILE)
    codigo_pais = forms.ChoiceField(
        choices=[
            ('+56', '🇨🇱 +56 (Chile)'),
        ],
        initial='+56',
        required=True,
        label='Código País',
        widget=forms.Select(attrs={
            'class': 'px-3 py-3 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-primary focus:border-transparent transition bg-gray-50',
            'style': 'width: 120px;'
        })
    )
    
    telefono = forms.CharField(
        max_length=15,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'flex-1 px-4 py-3 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
            'placeholder': '9 1234 5678',
            'pattern': '[0-9]{9}',
            'title': 'Ingresa 9 dígitos (ejemplo: 912345678)'
        }),
        error_messages={
            'required': 'El teléfono es obligatorio para repartidores.'
        }
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'codigo_pais', 'telefono', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES, 
                'placeholder': 'Nombre de usuario'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Confirmar contraseña'
        })
    
    def clean_telefono(self):
        """Validar formato del teléfono chileno"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if not telefono:
            raise ValidationError('El teléfono es obligatorio para repartidores.')
        
        telefono_limpio = telefono.replace(' ', '').replace('-', '')
        
        if not telefono_limpio.isdigit():
            raise ValidationError('El teléfono debe contener solo números.')
        
        if len(telefono_limpio) != 9:
            raise ValidationError('El teléfono debe tener exactamente 9 dígitos.')
        
        if not telefono_limpio.startswith('9'):
            raise ValidationError('El número de celular debe comenzar con 9.')
        
        return telefono
    
    def save(self, commit=True):
        """Guardar repartidor con teléfono completo"""
        user = super().save(commit=False)
        user.rol = 'repartidor'
        
        # Combinar código de país con teléfono
        codigo = self.cleaned_data.get('codigo_pais', '+56')
        telefono = self.cleaned_data.get('telefono', '').strip()
        user.telefono = f"{codigo} {telefono}"
        
        if commit:
            user.save()
        return user


# ========== OTROS FORMULARIOS ==========

class ReclamoForm(forms.ModelForm):
    class Meta:
        model = Reclamo
        fields = ['motivo', 'descripcion']
        widgets = {
            'motivo': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded-lg p-2', 'rows': 4}),
        }


class ResenaForm(forms.ModelForm):
    """Formulario para crear/editar reseñas de productos"""
    
    calificacion = forms.ChoiceField(
        label='Calificación',
        choices=[(i, f"{i} {'⭐' * i}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={
            'class': 'flex gap-2'
        }),
        help_text='Selecciona tu calificación'
    )
    
    comentario = forms.CharField(
        label='Comentario (opcional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA_CLASSES,
            'rows': 4,
            'placeholder': 'Cuéntanos tu experiencia con este producto...'
        })
    )
    
    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']
    
    def clean_comentario(self):
        """Validar longitud del comentario"""
        comentario = self.cleaned_data.get('comentario', '')
        if comentario and len(comentario) < 10:
            raise ValidationError('El comentario debe tener al menos 10 caracteres.')
        return comentario