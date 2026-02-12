from django import forms
from .models import InspectionSchedule

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
        fields = ['year', 'area', 'inspection_type', 'frequency', 'scheduled_date', 'responsible', 'observations']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

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
        fields = ['inspection_date', 'area', 'inspector_role', 'general_status', 'observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

class ExtinguisherItemForm(forms.ModelForm):
    class Meta:
        model = ExtinguisherItem
        exclude = ['inspection']
        widgets = {
            'last_recharge_date': forms.DateInput(attrs={'type': 'date'}),
            'next_recharge_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 2}),
        }

ExtinguisherItemFormSet = inlineformset_factory(
    ExtinguisherInspection, ExtinguisherItem,
    fields=['location', 'extinguisher_type', 'capacity', 'last_recharge_date', 'next_recharge_date', 
            'pressure_gauge_ok', 'safety_pin_ok', 'hose_nozzle_ok', 'signage_ok', 'access_ok', 'label_ok', 
            'status', 'observations'],
    extra=1, # Start with 1 row for dynamic addition
    can_delete=True,
    widgets={
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
        fields = ['inspection_date', 'area', 'inspector_role', 'general_status', 'observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

class FirstAidItemForm(forms.ModelForm):
    class Meta:
        model = FirstAidItem
        exclude = ['inspection']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 2}),
        }

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
        fields = ['inspection_date', 'area', 'inspector_role', 'inspected_process', 'general_status', 'observations']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

ProcessItemFormSet = inlineformset_factory(
    ProcessInspection, ProcessCheckItem,
    fields=['question', 'response', 'item_status', 'observations'],
    extra=0, # We will populate this in the view
    can_delete=False, # Standard questions shouldn't be deleted usually
    widgets={
        'question': forms.TextInput(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background: transparent;'}),
        'observations': forms.Textarea(attrs={'rows': 1}),
    }
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
