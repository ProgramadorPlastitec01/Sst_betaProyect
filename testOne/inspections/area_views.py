# Area Management Views
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Area
from django import forms

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: PRODUCCIÓN INDUSTRIAL'
            }),
        }
        labels = {
            'name': 'Nombre del Área',
            'is_active': 'Área Activa',
        }

class AreaListView(LoginRequiredMixin, ListView):
    model = Area
    template_name = 'inspections/area_list.html'
    context_object_name = 'areas'
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_areas'] = Area.objects.count()
        context['active_areas'] = Area.objects.filter(is_active=True).count()
        context['inactive_areas'] = Area.objects.filter(is_active=False).count()
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context

class AreaCreateView(LoginRequiredMixin, CreateView):
    model = Area
    form_class = AreaForm
    template_name = 'inspections/area_form.html'
    success_url = reverse_lazy('area_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Área "{form.instance.name}" creada exitosamente')
        return response

class AreaUpdateView(LoginRequiredMixin, UpdateView):
    model = Area
    form_class = AreaForm
    template_name = 'inspections/area_form.html'
    success_url = reverse_lazy('area_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Área "{form.instance.name}" actualizada correctamente')
        return response
