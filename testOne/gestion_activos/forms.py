from django import forms
from .models import Asset, ExtintorDetail, MontacargasDetail, AssetType, TipoExtintor


class AssetTypeForm(forms.ModelForm):
    class Meta:
        model = AssetType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del tipo'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
        }
        labels = {
            'name': 'Nombre',
            'description': 'Descripción',
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['code', 'asset_type', 'area', 'fecha_adquisicion', 'activo', 'observaciones']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único del activo'}),
            'asset_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_asset_type'}),
            'area': forms.Select(attrs={'class': 'form-control'}),
            'fecha_adquisicion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar tipos de activo que tienen lógica implementada
        self.fields['asset_type'].queryset = AssetType.objects.all()


class ExtintorDetailForm(forms.ModelForm):
    class Meta:
        model = ExtintorDetail
        fields = ['tipo_agente', 'capacidad_kg', 'fecha_recarga', 'fecha_vencimiento']
        widgets = {
            'tipo_agente': forms.Select(attrs={'class': 'form-control'}),
            'capacidad_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'fecha_recarga': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = TipoExtintor.objects.filter(activo=True)
        self.fields['tipo_agente'].queryset = qs
        self.fields['tipo_agente'].empty_label = 'Seleccionar tipo de extintor...'
        if not qs.exists():
            self.fields['tipo_agente'].help_text = (
                'No hay tipos de extintor configurados. '
                'Agregue tipos desde Configuración → Tipos de Extintor.'
            )


class MontacargasDetailForm(forms.ModelForm):
    class Meta:
        model = MontacargasDetail
        fields = ['marca', 'modelo', 'numero_serie', 'capacidad_carga_kg',
                  'fecha_ultimo_mantenimiento', 'fecha_proximo_mantenimiento']
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de serie'}),
            'capacidad_carga_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'fecha_ultimo_mantenimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_proximo_mantenimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TipoExtintorForm(forms.ModelForm):
    class Meta:
        model = TipoExtintor
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Polvo químico seco (PQS)'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del tipo',
            'activo': 'Activo',
        }
