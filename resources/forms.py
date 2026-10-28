# resources/forms.py
from django import forms
from .models import Recursos
from dashboard.models import EntregaAlumno  # ✅ Importar desde dashboard

class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recursos
        fields = ['titulo', 'descripcion', 'archivo', 'completado', 'fecha_completado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del recurso'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del recurso'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'fecha_completado': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class EntregaAlumnoForm(forms.ModelForm):
    class Meta:
        model = EntregaAlumno
        fields = ['titulo', 'archivo']  # Solo estos campos básicos
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Título de tu entrega',
                'required': True
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'required': True
            }),
        }