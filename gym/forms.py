from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Rutina, DetalleRutina, ProgresoFisico, PerfilUsuario


class RegistroForm(UserCreationForm):
    """Formulario de registro sin restricciones"""
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (opcional)'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
        
        # Quitar todas las validaciones de contraseña
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].help_text = None
    
    def clean_password1(self):
        """Validación mínima: 8 caracteres"""
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')
        return password1
    
    def clean_password2(self):
        """Verificar que coincidan"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2
    
    def _post_clean(self):
        """Deshabilitar validaciones complejas de Django pero mantener la básica"""
        super(forms.ModelForm, self)._post_clean()


class RutinaForm(forms.ModelForm):
    """Formulario de rutina"""
    class Meta:
        model = Rutina
        fields = ['nombre', 'descripcion', 'dificultad', 'duracion_min', 'objetivo', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la rutina'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
            'dificultad': forms.Select(attrs={'class': 'form-control'}),
            'duracion_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutos'}),
            'objetivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Objetivo de la rutina'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DetalleRutinaForm(forms.ModelForm):
    """Formulario para agregar ejercicios a rutina"""
    class Meta:
        model = DetalleRutina
        fields = ['ejercicio', 'orden', 'series', 'repeticiones', 'peso', 'descanso_seg', 'notas']
        widgets = {
            'ejercicio': forms.Select(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Orden'}),
            'series': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Series'}),
            'repeticiones': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Reps'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso (kg)', 'step': '0.5'}),
            'descanso_seg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Descanso (seg)'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas'}),
        }


class ProgresoForm(forms.ModelForm):
    """Formulario de progreso físico"""
    class Meta:
        model = ProgresoFisico
        fields = ['peso', 'grasa_corporal', 'masa_muscular', 'cintura', 'pecho', 'brazos', 'piernas', 'notas']
        widgets = {
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso (kg)', 'step': '0.1'}),
            'grasa_corporal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '%', 'step': '0.1'}),
            'masa_muscular': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kg', 'step': '0.1'}),
            'cintura': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.1'}),
            'pecho': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.1'}),
            'brazos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.1'}),
            'piernas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.1'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas'}),
        }


class PerfilForm(forms.ModelForm):
    """Formulario de perfil de usuario"""
    class Meta:
        model = PerfilUsuario
        fields = ['foto_perfil', 'telefono', 'fecha_nacimiento', 'altura', 'peso_actual', 'nivel_experiencia', 'objetivo']
        widgets = {
            'foto_perfil': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL de foto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'altura': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm'}),
            'peso_actual': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kg', 'step': '0.1'}),
            'nivel_experiencia': forms.Select(attrs={'class': 'form-control'}),
            'objetivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tus objetivos'}),
        }
