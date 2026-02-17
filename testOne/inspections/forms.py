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
    year = forms.ChoiceField(label="Año de Programación")

    class Meta:
        model = InspectionSchedule
        fields = ['year', 'area', 'inspection_type', 'frequency', 'scheduled_date', 'responsible', 'observations']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import date
        current_year = date.today().year
        self.fields['year'].choices = [(current_year, str(current_year)), (current_year + 1, str(current_year + 1))]
        self.fields['year'].initial = current_year
        
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
        fields = ['year', 'area', 'inspection_type', 'frequency', 'scheduled_date', 'responsible', 'status', 'observations']

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
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # Set default date to today if not provided
        if not self.instance.pk:
            # Check if initial is set, otherwise use today
            if 'inspection_date' not in self.initial:
                today = timezone.now().strftime('%Y-%m-%d')
                self.fields['inspection_date'].initial = today
                # Explicitly set value attribute for HTML5 date input
                self.fields['inspection_date'].widget.attrs['value'] = today
            
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
            'last_recharge_date': forms.DateInput(attrs={'type': 'date'}),
            'next_recharge_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        observations = cleaned_data.get('observations')

        if status == 'Malo' and not observations:
            self.add_error('observations', 'La observación es obligatoria para ítems en estado Malo.')

        return cleaned_data

ExtinguisherItemFormSet = inlineformset_factory(
    ExtinguisherInspection, ExtinguisherItem,
    fields=['extinguisher_number', 'location', 'extinguisher_type', 'capacity', 'last_recharge_date', 'next_recharge_date', 
            'pressure_gauge_ok', 'safety_pin_ok', 'hose_nozzle_ok', 'signage_ok', 'access_ok', 'label_ok', 
            'status', 'observations'],
    extra=1, # Start with 1 row for dynamic addition
    can_delete=True,
    widgets={
        'extinguisher_number': forms.TextInput(attrs={'placeholder': 'Número'}),
        'location': forms.TextInput(attrs={'placeholder': 'Ubicación'}),
        'capacity': forms.TextInput(attrs={'placeholder': 'Capacidad'}),
        'last_recharge_date': forms.DateInput(attrs={'type': 'date'}),
        'next_recharge_date': forms.DateInput(attrs={'type': 'date'}),
        'observations': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Observaciones'}),
    }
)

# 2. First Aid Forms
class FirstAidInspectionForm(forms.ModelForm):
    class Meta:
        model = FirstAidInspection
        fields = ['inspection_date', 'area', 'inspector_role']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # Set default date to today if not provided
        if not self.instance.pk:
            if 'inspection_date' not in self.initial:
                today = timezone.now().strftime('%Y-%m-%d')
                self.fields['inspection_date'].initial = today
                self.fields['inspection_date'].widget.attrs['value'] = today
            
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
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        observations = cleaned_data.get('observations')

        if status == 'No Existe' and not observations:
            self.add_error('observations', 'La observación es obligatoria para ítems que "No Existen".')

        return cleaned_data

FirstAidItemFormSet = inlineformset_factory(
    FirstAidInspection, FirstAidItem,
    fields=['element_name', 'quantity', 'expiration_date', 'status', 'observations'],
    extra=1, # Start with 1 row, let user add more dynamically
    can_delete=True,
    widgets={
        'element_name': forms.TextInput(attrs={'placeholder': 'Nombre del elemento'}),
        'quantity': forms.NumberInput(attrs={'min': 0}),
        'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        'observations': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Observaciones'}),
    }
)

# 3. Process Forms
class ProcessInspectionForm(forms.ModelForm):
    class Meta:
        model = ProcessInspection
        fields = ['inspection_date', 'area', 'inspector_role', 'inspected_process', 'additional_observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'additional_observations': forms.Textarea(attrs={'rows': 3}),
            'area': forms.HiddenInput(), # Hidden as per user request
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If area is not in initial (manual creation without schedule) and not an existing instance with area, make it visible.
        # This handles the user request to hide it in the header when coming from schedule, but allows selection if manual.
        if not self.initial.get('area') and not (self.instance and self.instance.pk and getattr(self.instance, 'area_id', None)):
            self.fields['area'].widget = forms.Select()
            self.fields['area'].queryset = self.fields['area'].queryset # Ensure queryset is kept


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
        
        # Ensure observations is treated as string and stripped
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
class StorageInspectionForm(forms.ModelForm):
    class Meta:
        model = StorageInspection
        fields = ['inspection_date', 'area', 'inspector_role', 'inspected_process', 'general_status', 'observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

StorageItemFormSet = inlineformset_factory(
    StorageInspection, StorageCheckItem,
    fields=['question', 'response', 'item_status', 'observations'],
    extra=0, 
    can_delete=False,
    widgets={
        'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
        'observations': forms.Textarea(attrs={'rows': 1}),
    }
)

# 5. Forklift Forms
class ForkliftInspectionForm(forms.ModelForm):
    class Meta:
        model = ForkliftInspection
        fields = ['inspection_date', 'area', 'forklift_type', 'general_status', 'observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].queryset = Area.objects.filter(is_active=True).order_by('name')
        self.fields['area'].empty_label = "Seleccione un área"

ForkliftItemFormSet = inlineformset_factory(
    ForkliftInspection, ForkliftCheckItem,
    fields=['question', 'response', 'observations'],
    extra=0, 
    can_delete=False,
    widgets={
        'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
        'observations': forms.Textarea(attrs={'rows': 1}),
    }
)
