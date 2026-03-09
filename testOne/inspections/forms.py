from django import forms
from .models import InspectionSchedule, Area
import json


class AssetSelect(forms.Select):
    """
    Select widget que inyecta data-* attributes en cada <option>
    para mostrar preview del activo sin necesitar AJAX.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value and hasattr(value, 'instance'):
            asset = value.instance
            ext_detail = getattr(asset, 'extintor_detail', None)
            mnt_detail = getattr(asset, 'montacargas_detail', None)
            
            option['attrs']['data-code'] = asset.code
            option['attrs']['data-area'] = str(asset.area) if asset.area else '-'
            option['attrs']['data-estado'] = asset.estado_label
            
            if ext_detail:
                option['attrs']['data-cap'] = f"{ext_detail.capacidad_kg} lbs"
                option['attrs']['data-tipo'] = str(ext_detail.tipo_agente) if ext_detail.tipo_agente else '-'
                option['attrs']['data-ultima-recarga'] = str(ext_detail.fecha_recarga) if ext_detail.fecha_recarga else '-'
                option['attrs']['data-recarga'] = str(ext_detail.fecha_vencimiento) if ext_detail.fecha_vencimiento else '-'
            elif mnt_detail:
                option['attrs']['data-marca'] = mnt_detail.marca
                option['attrs']['data-modelo'] = mnt_detail.modelo
                option['attrs']['data-fuel'] = mnt_detail.tipo_montacargas
                option['attrs']['data-proximo-mnt'] = str(mnt_detail.fecha_proximo_mantenimiento)
            
            # Build searchable text for filtering
            search_terms = [asset.code, str(asset.area) if asset.area else '']
            if ext_detail:
                search_terms.append(str(ext_detail.tipo_agente) if ext_detail.tipo_agente else '')
            elif mnt_detail:
                search_terms.extend([mnt_detail.marca, mnt_detail.modelo, mnt_detail.tipo_montacargas])
                
            option['attrs']['data-search'] = ' '.join(search_terms).lower()
        return option


class InspectionScheduleForm(forms.ModelForm):
    TYPE_CHOICES = [
        ('Extintores', 'Extintores'),
        ('Botiquines', 'Botiquines'),
        ('Instalaciones de Proceso', 'Instalaciones de Proceso'),
        ('Almacenamiento', 'Almacenamiento'),
        ('Montacargas', 'Montacargas'),
    ]
    inspection_type = forms.ChoiceField(choices=TYPE_CHOICES, label="Tipo de Inspección")

    class Meta:
        model = InspectionSchedule
        fields = ['area', 'inspection_type', 'frequency', 'scheduled_date', 'observations']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

class InspectionUpdateForm(forms.ModelForm):
    TYPE_CHOICES = [
        ('Extintores', 'Extintores'),
        ('Botiquines', 'Botiquines'),
        ('Instalaciones de Proceso', 'Instalaciones de Proceso'),
        ('Almacenamiento', 'Almacenamiento'),
        ('Montacargas', 'Montacargas'),
    ]
    inspection_type = forms.ChoiceField(choices=TYPE_CHOICES, label="Tipo de Inspección")

    class Meta:
        model = InspectionSchedule
        fields = ['area', 'inspection_type', 'frequency', 'scheduled_date', 'status', 'observations']

        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

# --- New Inspection Modules ---
from django.forms import inlineformset_factory
from .models import (
    ExtinguisherInspection, ExtinguisherItem,
    FirstAidInspection, FirstAidItem,
    ProcessInspection, ProcessCheckItem,
    StorageInspection, StorageCheckItem,
    ForkliftInspection, ForkliftCheckItem
)

# 1. Extinguisher Forms
class ExtinguisherInspectionForm(forms.ModelForm):
    class Meta:
        model = ExtinguisherInspection
        fields = ['inspection_date', 'area', 'inspector_role']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        # 1. Date Logic
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                self.fields['inspection_date'].initial = timezone.now().date()

        if self.instance.pk and self.instance.inspection_date:
            self.fields['inspection_date'].widget.attrs['value'] = self.instance.inspection_date.strftime('%Y-%m-%d')

        # 2. Inspector Role Logic: Match with user profile
        if self.user:
            user_role_name = self.user.get_role_name()
            role_choices = [c[0] for c in self.fields['inspector_role'].choices]

            if user_role_name in role_choices:
                self.fields['inspector_role'].initial = user_role_name
                self.fields['inspector_role'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #f8f9fa; border-color: #e2e8f0;'
                })

        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

        # Lock area if provided (e.g. from schedule)
        if self.initial.get('area'):
            self.fields['area'].widget.attrs.update({
                'style': 'pointer-events: none; background-color: #e9ecef;',
                'readonly': 'readonly'
            })
class ExtinguisherItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from gestion_activos.models import Asset, AssetType
        try:
            tipo_extintor = AssetType.objects.get(name='Extintor')
            qs = Asset.objects.filter(
                asset_type=tipo_extintor, activo=True, extintor_detail__estado_movimiento='NORMAL'
            ).select_related('area', 'extintor_detail__tipo_agente').order_by('code')
        except AssetType.DoesNotExist:
            qs = Asset.objects.none()
        self.fields['asset'].queryset = qs
        self.fields['asset'].required = True
        self.fields['asset'].empty_label = '--- Seleccione extintor ---'
        self.fields['asset'].label = 'Extintor'

        # Disable asset change on update
        if self.instance.pk:
            self.fields['asset'].disabled = True
            self.fields['asset'].required = False
            
            if self.instance.fecha_recarga_realizada:
                self.fields['fecha_recarga_realizada'].widget.attrs['value'] = self.instance.fecha_recarga_realizada.strftime('%Y-%m-%d')
            if self.instance.fecha_proxima_recarga:
                self.fields['fecha_proxima_recarga'].widget.attrs['value'] = self.instance.fecha_proxima_recarga.strftime('%Y-%m-%d')

    class Meta:
        model = ExtinguisherItem
        exclude = ['inspection', 'registered_by']
        widgets = {
            'asset': AssetSelect(attrs={
                'class': 'form-control asset-item-select',
                'style': 'width: 100%;',
            }),
            'observations': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Observaciones...', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'fecha_recarga_realizada': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control js-recharge-date',
                    'placeholder': 'DD/MM/AAAA',
                }
            ),
            'fecha_proxima_recarga': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control js-next-recharge-date',
                    'placeholder': 'DD/MM/AAAA',
                    'readonly': 'readonly',
                    'style': 'background-color: #f8f9fa;'
                }
            ),
        }

    def clean_asset(self):
        # Return existing asset if field is disabled
        if self.instance.pk:
            return self.instance.asset
        return self.cleaned_data.get('asset')

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        observations = cleaned_data.get('observations')
        if status == 'Malo' and not observations:
            self.add_error('observations', 'La observación es obligatoria para ítems en estado Malo.')
        return cleaned_data

ExtinguisherItemFormSet = inlineformset_factory(
    ExtinguisherInspection, ExtinguisherItem,
    form=ExtinguisherItemForm,
    extra=1,
    can_delete=True
)

# 2. First Aid Forms
class FirstAidInspectionForm(forms.ModelForm):
    class Meta:
        model = FirstAidInspection
        fields = ['inspection_date', 'area', 'inspector_role']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # 1. Date Logic
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                self.fields['inspection_date'].initial = timezone.now().date()
        
        if self.instance.pk and self.instance.inspection_date:
            self.fields['inspection_date'].widget.attrs['value'] = self.instance.inspection_date.strftime('%Y-%m-%d')
        
        # 2. Inspector Role Logic
        if self.user:
            user_role_name = self.user.get_role_name()
            role_choices = [c[0] for c in self.fields['inspector_role'].choices]
            
            if user_role_name in role_choices:
                self.fields['inspector_role'].initial = user_role_name
                self.fields['inspector_role'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #f8f9fa; border-color: #e2e8f0;'
                })
            
        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"
        
        # Lock area if provided (e.g. from schedule)
        if self.initial.get('area'):
            self.fields['area'].widget.attrs.update({
                'style': 'pointer-events: none; background-color: #e9ecef;',
                'readonly': 'readonly'
            })

class FirstAidItemForm(forms.ModelForm):
    # Permitir cantidad 0: PositiveIntegerField de Django valida >= 1,
    # se sobrescribe con IntegerField(min_value=0) para registrar elementos sin stock.
    quantity = forms.IntegerField(
        min_value=0,
        label="Cantidad (Unidad)",
        widget=forms.NumberInput(attrs={'min': 0})
    )

    class Meta:
        model = FirstAidItem
        exclude = ['inspection', 'registered_by']
        widgets = {
            'element_name': forms.TextInput(attrs={'placeholder': 'Nombre del elemento'}),
            'expiration_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'observations': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Observaciones'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.expiration_date:
            self.fields['expiration_date'].widget.attrs['value'] = self.instance.expiration_date.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        observations = cleaned_data.get('observations')

        if status == 'No Existe' and not observations:
            self.add_error('observations', 'La observación es obligatoria para ítems que "No Existen".')

        return cleaned_data

FirstAidItemFormSet = inlineformset_factory(
    FirstAidInspection, FirstAidItem,
    form=FirstAidItemForm,
    extra=1, # Start with 1 row, let user add more dynamically
    can_delete=True
)

# 3. Process Forms
class ProcessInspectionForm(forms.ModelForm):
    class Meta:
        model = ProcessInspection
        fields = ['inspection_date', 'area', 'inspector_role', 'inspected_process', 'additional_observations']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'additional_observations': forms.Textarea(attrs={'rows': 3}),
            'area': forms.HiddenInput(), # Hidden as per user request
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # 1. Date Logic
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                self.fields['inspection_date'].initial = timezone.now().date()
        
        if self.instance.pk and self.instance.inspection_date:
            self.fields['inspection_date'].widget.attrs['value'] = self.instance.inspection_date.strftime('%Y-%m-%d')
        
        # 2. Inspector Role Logic
        if self.user:
            user_role_name = self.user.get_role_name()
            role_choices = [c[0] for c in self.fields['inspector_role'].choices]
            
            if user_role_name in role_choices:
                self.fields['inspector_role'].initial = user_role_name
                self.fields['inspector_role'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #f8f9fa; border-color: #e2e8f0;'
                })

        # If area is not in initial (manual creation without schedule) and not an existing instance with area, make it visible.
        if not self.initial.get('area') and not (self.instance and self.instance.pk and getattr(self.instance, 'area_id', None)):
            self.fields['area'].widget = forms.Select()
            self.fields['area'].queryset = self.fields['area'].queryset # Ensure queryset is kept

        # 3. Hacer obligatorio el campo Proceso Inspeccionado
        self.fields['inspected_process'].required = True
        self.fields['inspected_process'].widget.attrs.update({
            'placeholder': 'Ej: Línea de producción, Área de envasado, etc.'
        })

class ProcessCheckItemForm(forms.ModelForm):
    class Meta:
        model = ProcessCheckItem
        fields = ['question', 'response', 'item_status', 'observations']
        widgets = {
            'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
            'item_status': forms.Select(attrs={'class': 'js-status-select form-control', 'style': 'min-width: 100px;'}),
            'observations': forms.Textarea(attrs={'class': 'js-obs-input form-control', 'rows': 1, 'placeholder': 'Observaciones'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('item_status')
        observations = cleaned_data.get('observations')
        
        if observations is None:
            observations = ''
            
        if status == 'Malo' and not observations.strip():
            self.add_error('observations', 'La observación es obligatoria para ítems en estado Malo.')

        return cleaned_data

ProcessItemFormSet = inlineformset_factory(
    ProcessInspection, ProcessCheckItem,
    form=ProcessCheckItemForm,
    extra=0, 
    can_delete=False,
)

# 4. Storage Forms
class StorageCheckItemForm(forms.ModelForm):
    class Meta:
        model = StorageCheckItem
        fields = ['question', 'response', 'item_status', 'observations']
        widgets = {
            'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
            'item_status': forms.Select(attrs={'class': 'js-status-select form-control', 'style': 'min-width: 100px;'}),
            'observations': forms.Textarea(attrs={'class': 'js-obs-input form-control', 'rows': 1, 'placeholder': 'Observaciones'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('item_status')
        observations = cleaned_data.get('observations')
        
        if observations is None:
            observations = ''
            
        if status == 'Malo' and not observations.strip():
            self.add_error('observations', 'La observación es obligatoria para ítems en estado Malo.')

        return cleaned_data

class StorageInspectionForm(forms.ModelForm):
    class Meta:
        model = StorageInspection
        fields = ['inspection_date', 'area', 'inspector_role', 'inspected_process', 'additional_observations']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'additional_observations': forms.Textarea(attrs={'rows': 3}),
            'area': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # 1. Date Logic
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                self.fields['inspection_date'].initial = timezone.now().date()
        
        if self.instance.pk and self.instance.inspection_date:
            self.fields['inspection_date'].widget.attrs['value'] = self.instance.inspection_date.strftime('%Y-%m-%d')

        # 2. Inspector Role Logic
        if self.user:
            user_role_name = self.user.get_role_name()
            role_choices = [c[0] for c in self.fields['inspector_role'].choices]
            
            if user_role_name in role_choices:
                self.fields['inspector_role'].initial = user_role_name
                self.fields['inspector_role'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #f8f9fa; border-color: #e2e8f0;'
                })

        if not self.initial.get('area') and not (self.instance and self.instance.pk and getattr(self.instance, 'area_id', None)):
            self.fields['area'].widget = forms.Select()
            self.fields['area'].queryset = self.fields['area'].queryset

        # 3. Hacer obligatorio el campo Proceso/Área Inspeccionada
        self.fields['inspected_process'].required = True
        self.fields['inspected_process'].widget.attrs.update({
            'placeholder': 'Ej: Almacén de materia prima, Bodega 1, etc.'
        })

StorageItemFormSet = inlineformset_factory(
    StorageInspection, StorageCheckItem,
    form=StorageCheckItemForm,
    extra=0, 
    can_delete=False,
)

# 5. Forklift Forms
# 5. Forklift Forms
class ForkliftCheckItemForm(forms.ModelForm):
    class Meta:
        model = ForkliftCheckItem
        fields = ['question', 'response', 'item_status', 'observations']
        widgets = {
            'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
            'item_status': forms.Select(attrs={'class': 'js-status-select form-control', 'style': 'min-width: 100px;'}),
            'observations': forms.Textarea(attrs={'class': 'js-obs-input form-control', 'rows': 1, 'placeholder': 'Observaciones'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('item_status')
        observations = cleaned_data.get('observations')
        
        if observations is None:
            observations = ''
            
        if status == 'Malo' and not observations.strip():
            self.add_error('observations', 'La observación es obligatoria para ítems en estado Malo.')

        return cleaned_data

# 5. Forklift Forms
class ForkliftInspectionForm(forms.ModelForm):
    class Meta:
        model = ForkliftInspection
        fields = ['inspection_date', 'asset', 'area', 'inspector_role', 'additional_observations']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'asset': AssetSelect(attrs={
                'class': 'form-control asset-item-select',
                'style': 'width: 100%;',
                'id': 'id_asset_forklift'
            }),
            'additional_observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        from gestion_activos.models import Asset, AssetType
        
        # 1. Date Logic
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                self.fields['inspection_date'].initial = timezone.now().date()
        
        if self.instance.pk and self.instance.inspection_date:
            self.fields['inspection_date'].widget.attrs['value'] = self.instance.inspection_date.strftime('%Y-%m-%d')
        
        # 2. Inspector Role Logic
        if self.user:
            user_role_name = self.user.get_role_name()
            role_choices = [c[0] for c in self.fields['inspector_role'].choices]
            
            if user_role_name in role_choices:
                self.fields['inspector_role'].initial = user_role_name
                self.fields['inspector_role'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #f8f9fa; border-color: #e2e8f0;'
                })

        # 3. Asset Queryset (Only Forklifts)
        try:
            tipo_montacargas = AssetType.objects.get(name='Montacargas')
            # Permitir el actual si es una edición, sino solo activos/vencidos
            if self.instance.pk and self.instance.asset:
                qs = Asset.objects.filter(pk=self.instance.asset.pk)
                self.fields['asset'].disabled = True
            else:
                qs = Asset.objects.filter(
                    asset_type=tipo_montacargas,
                    activo=True
                ).select_related('area', 'montacargas_detail').order_by('code')
        except AssetType.DoesNotExist:
            qs = Asset.objects.none()
            
        self.fields['asset'].queryset = qs
        self.fields['asset'].required = True
        self.fields['asset'].empty_label = '--- Seleccione un Montacargas ---'

        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

        # Lock area if provided (e.g. from schedule)
        if self.initial.get('area'):
            self.fields['area'].widget.attrs.update({
                'style': 'pointer-events: none; background-color: #e9ecef;',
                'readonly': 'readonly'
            })

    def clean_asset(self):
        asset = self.cleaned_data.get('asset')
        if not self.instance.pk: # Only on creation
            if asset:
                estado = asset.estado_actual
                if estado in ['FUERA_DE_SERVICIO', 'REEMPLAZADO']:
                    raise forms.ValidationError(f"No se puede inspeccionar un montacargas en estado: {asset.estado_label}")
        return asset

ForkliftItemFormSet = inlineformset_factory(
    ForkliftInspection, ForkliftCheckItem,
    form=ForkliftCheckItemForm,
    extra=0, 
    can_delete=False,
)
