from django import forms
from .models import InspectionSchedule, Area

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
        
        # Ensure correct formatting for HTML5 date input on edit
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
    class Meta:
        model = ExtinguisherItem
        exclude = ['inspection']
        widgets = {
            'extinguisher_number': forms.NumberInput(attrs={'placeholder': 'Número'}),
            'location': forms.TextInput(attrs={'placeholder': 'Ubicación'}),
            'capacity': forms.TextInput(attrs={'placeholder': 'Capacidad'}),
            'last_recharge_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'next_recharge_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'observations': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Observaciones'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            if self.instance.last_recharge_date:
                self.fields['last_recharge_date'].widget.attrs['value'] = self.instance.last_recharge_date.strftime('%Y-%m-%d')
            if self.instance.next_recharge_date:
                self.fields['next_recharge_date'].widget.attrs['value'] = self.instance.next_recharge_date.strftime('%Y-%m-%d')

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
    extra=1, # Start with 1 row for dynamic addition
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
    class Meta:
        model = FirstAidItem
        exclude = ['inspection']
        widgets = {
            'element_name': forms.TextInput(attrs={'placeholder': 'Nombre del elemento'}),
            'quantity': forms.NumberInput(attrs={'min': 0}),
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
        fields = ['inspection_date', 'area', 'inspector_role', 'forklift_type', 'additional_observations']
        widgets = {
            'inspection_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'additional_observations': forms.Textarea(attrs={'rows': 3}),
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

ForkliftItemFormSet = inlineformset_factory(
    ForkliftInspection, ForkliftCheckItem,
    form=ForkliftCheckItemForm,
    extra=0, 
    can_delete=False,
)
