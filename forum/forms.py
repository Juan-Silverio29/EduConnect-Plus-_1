from django import forms
from .models import Foro, Comentario

class ForoForm(forms.ModelForm):
    class Meta:
        model = Foro
        fields = ["titulo", "descripcion", "archivo"]  # 👈 añadimos archivo
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Escribe el título del tema"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "placeholder": "Escribe la descripción"}),
        }

    # Campo de archivo con estilos
    archivo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )


class ComentarioForm(forms.ModelForm):
    # Campo opcional para subir archivo
    archivo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".pdf,.jpg,.png,.jpeg,.docx,.xlsx,.txt"
        })
    )

    class Meta:
        model = Comentario
        fields = ["texto", "archivo"]
        widgets = {
            "texto": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu comentario..."
            }),
        }
