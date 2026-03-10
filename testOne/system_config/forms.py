from django import forms
from .models import Plano

class PlanoForm(forms.ModelForm):
    class Meta:
        model = Plano
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PL1P1'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'nombre': 'Nombre del Plano',
            'activo': 'Activo'
        }
