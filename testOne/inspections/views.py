from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db import transaction, models
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import (
    InspectionSchedule,
    ExtinguisherInspection, ExtinguisherItem, 
    FirstAidInspection, FirstAidItem,
    ProcessInspection, StorageInspection,
    ForkliftInspection, ForkliftCheckItem
)
from dateutil.relativedelta import relativedelta
from .forms import (
    InspectionScheduleForm, InspectionUpdateForm,
    ExtinguisherInspectionForm, ExtinguisherItemFormSet, ExtinguisherItemForm,
    FirstAidInspectionForm, FirstAidItemFormSet, FirstAidItemForm,
    ProcessInspectionForm, ProcessItemFormSet,
    StorageInspectionForm, StorageItemFormSet,
    ForkliftInspectionForm, ForkliftItemFormSet
)

# --- Mixin to provide matrix context to any view ---
class MatrixContextMixin:
    def get_context_data(self, **kwargs):
        from datetime import date
        context = super().get_context_data(**kwargs)
        current_year = date.today().year

        # Pass unique values for filters with pre-calculated selection state
        # Default to current year if not specified in GET (initial load)
        # If specified but empty (?year=), it means 'All'
        get_year = self.request.GET.get('year')
        selected_year = str(current_year) if get_year is None else get_year
        
        selected_area = self.request.GET.get('area', '')
        
        years_qs = InspectionSchedule.objects.values_list('year', flat=True).distinct().order_by('-year')
        context['years_data'] = [{'val': str(y), 'selected': str(y) == selected_year} for y in years_qs]
        
        # FIX: Use area name instead of ID for dropdown
        areas_qs = InspectionSchedule.objects.values_list('area__id', 'area__name').distinct().order_by('area__name')
        try:
             sel_area_id = int(selected_area) if selected_area else None
        except ValueError:
             sel_area_id = None
        context['areas_data'] = [{'id': a[0], 'name': a[1], 'selected': a[0] == sel_area_id} for a in areas_qs]
        
        # Display year for the table header
        context['year_display'] = selected_year if selected_year else "Histórico Completo"
        
        context['statuses'] = InspectionSchedule.STATUS_CHOICES
        
        # FORM FOR MODAL - FIXING THE EMPTY FORM ISSUE
        context['form'] = InspectionScheduleForm()
        
        # Base Queryset for Matrix (respect filters if present)
        matrix_qs = InspectionSchedule.objects.all()
        
        # Apply filters
        if selected_year: 
            matrix_qs = matrix_qs.filter(year=selected_year)
            
        # FIX: Filter by area name
        if selected_area: 
            matrix_qs = matrix_qs.filter(area__id=selected_area)

        model_mapping = {
            'Extintores': ExtinguisherInspection,
            'Botiquines': FirstAidInspection,
            'Instalaciones de Proceso': ProcessInspection,
            'Almacenamiento': StorageInspection,
            'Montacargas': ForkliftInspection,
        }
        
        evidence_mapping = {
            'Extintores': 'Inspección de extintores (R-RH-SST-019)',
            'Botiquines': 'Inspección de Botiquines (R-RH-SST-020)',
            'Instalaciones de Proceso': 'Inspección de Instalaciones (R-RH-SST-030)',
            'Almacenamiento': 'Inspección Almacenamiento (R-RH-SST-031)',
            'Montacargas': 'Inspección de Montacargas (R-RH-SST-022)',
        }

        base_types = ['Extintores', 'Botiquines', 'Instalaciones de Proceso', 'Almacenamiento', 'Montacargas']
        found_types = list(matrix_qs.values_list('inspection_type', flat=True).distinct())
        all_types = sorted(list(set(base_types + found_types)))
        
        matrix = []
        months_range = range(1, 13)
        months_names = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEPT', 'OCT', 'NOV', 'DIC']

        for t in all_types:
            type_qs = matrix_qs.filter(inspection_type=t)
            row_cells = []
            total_p = 0
            total_e = 0
            actual_model = model_mapping.get(t)
            
            # Get responsible from the first schedule item found for this type
            first_item = type_qs.first()
            responsible_name = first_item.responsible.get_full_name() if first_item and first_item.responsible else "Equipo SST"

            for m in months_range:
                p_items = type_qs.filter(scheduled_date__month=m)
                p_count = p_items.count()
                e_count = p_items.filter(status='Realizada').count()
                
                if actual_model:
                    actual_qs = actual_model.objects.filter(inspection_date__month=m)
                    if selected_year: actual_qs = actual_qs.filter(inspection_date__year=selected_year)
                    if selected_area: actual_qs = actual_qs.filter(area_id=selected_area)
                    unlinked_count = actual_qs.filter(schedule_item__isnull=True).count()
                    e_count += unlinked_count

                total_p += p_count
                total_e += e_count
                
                row_cells.append({
                    'm': m,
                    'p': p_count if p_count > 0 else '',
                    'e': e_count if e_count > 0 else ''
                })
            
            compliance = (total_e / total_p * 100) if total_p > 0 else (100 if total_e > 0 else 0)
            matrix.append({
                'type': t,
                'cells': row_cells,
                'total_p': total_p,
                'total_e': total_e,
                'compliance': round(compliance),
                'responsible': responsible_name,
                'evidence': evidence_mapping.get(t, 'SST Record')
            })

        context['matrix'] = matrix
        context['months_names'] = months_names
        
        # Bottom Summary Table
        summary_rows = []
        total_p_g = sum(item['total_p'] for item in matrix)
        total_e_g = sum(item['total_e'] for item in matrix)
        
        monthly_stats = []
        for m_idx in range(12):
            m_p = sum(item['cells'][m_idx]['p'] if isinstance(item['cells'][m_idx]['p'], int) else 0 for item in matrix)
            m_e = sum(item['cells'][m_idx]['e'] if isinstance(item['cells'][m_idx]['e'], int) else 0 for item in matrix)
            comp = (m_e / m_p * 100) if m_p > 0 else (100 if m_e > 0 else 0)
            monthly_stats.append({
                'p': m_p,
                'e': m_e,
                'compliance': round(comp)
            })
            
        context['monthly_stats'] = monthly_stats
        context['total_p_global'] = total_p_g
        context['total_e_global'] = total_e_g
        context['global_compliance'] = round((total_e_g / total_p_g * 100) if total_p_g > 0 else (100 if total_e_g > 0 else 0))
        
        return context

# --- Mixin to provide scheduled inspections to module list views ---
class ScheduledInspectionsMixin:
    """
    Mixin to add pending scheduled inspections to any inspection module list view.
    Automatically filters by inspection type based on the module.
    """
    # Map of module types to their inspection_type keywords
    INSPECTION_TYPE_MAP = {
        'extinguisher': 'extintor',
        'first_aid': 'botiquin',
        'process': 'proceso',
        'storage': 'almacenamiento',
        'forklift': 'montacarga',
    }
    
    # Override this in the view to specify which module type
    inspection_module_type = None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.inspection_module_type and self.inspection_module_type in self.INSPECTION_TYPE_MAP:
            keyword = self.INSPECTION_TYPE_MAP[self.inspection_module_type]
            
            qs = InspectionSchedule.objects.filter(
                inspection_type__icontains=keyword
            )
            
            schedule_id = self.request.GET.get('schedule_id')
            if schedule_id:
                qs = qs.filter(id=schedule_id)
            else:
                qs = qs.filter(status='Programada')
                
            context['scheduled_inspections'] = qs.select_related('responsible').order_by('scheduled_date')
        else:
            context['scheduled_inspections'] = InspectionSchedule.objects.none()
        
        return context

# 0. Core Schedule Views
class InspectionListView(LoginRequiredMixin, MatrixContextMixin, ListView):
    model = InspectionSchedule
    template_name = 'inspections/inspection_list.html'
    context_object_name = 'schedule'

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.GET.get('year')
        area = self.request.GET.get('area')
        if year: qs = qs.filter(year=year)
        if area: qs = qs.filter(area__id=area)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        year_filter = self.request.GET.get('year', '')
        area_filter = self.request.GET.get('area', '')
        
        # Consolidate all inspections from all modules
        all_inspections = []
        
        # Helper function to add inspections to list
        def add_inspections(model, inspection_type, detail_url_name):
            qs = model.objects.all()
            
            # Apply filters
            if year_filter:
                qs = qs.filter(inspection_date__year=int(year_filter))
            if area_filter:
                qs = qs.filter(area__id=area_filter)
            
            for insp in qs:
                all_inspections.append({
                    'id': insp.pk,
                    'date': insp.inspection_date,
                    'year': insp.inspection_date.year,
                    'area': insp.area,
                    'type': inspection_type,
                    'inspector': insp.inspector.get_full_name() if insp.inspector else 'N/A',
                    'status': insp.general_status,
                    'detail_url': reverse(detail_url_name, args=[insp.pk]),
                    'schedule_linked': insp.schedule_item is not None,
                })
        
        # Add inspections from each module
        add_inspections(ExtinguisherInspection, 'Extintores', 'extinguisher_detail')
        add_inspections(FirstAidInspection, 'Botiquines', 'first_aid_detail')
        add_inspections(ProcessInspection, 'Instalaciones de Proceso', 'process_detail')
        add_inspections(StorageInspection, 'Almacenamiento', 'storage_detail')
        add_inspections(ForkliftInspection, 'Montacargas', 'forklift_detail')
        
        # Sort by date descending
        all_inspections.sort(key=lambda x: x['date'], reverse=True)
        
        context['all_inspections'] = all_inspections
        
        # Get unique years and areas from actual inspections for filters
        all_years = set()
        all_areas = set()
        
        for model in [ExtinguisherInspection, FirstAidInspection, ProcessInspection, StorageInspection, ForkliftInspection]:
            years = model.objects.values_list('inspection_date__year', flat=True).distinct()
            all_years.update(years)
            areas = model.objects.values_list('area__id', 'area__name').distinct()
            all_areas.update(areas)
        
        # Also include years/areas from schedule
        schedule_years = InspectionSchedule.objects.values_list('year', flat=True).distinct()
        all_years.update(schedule_years)
        schedule_areas = InspectionSchedule.objects.values_list('area__id', 'area__name').distinct()
        all_areas.update(schedule_areas)
        
        # Update filter data with actual inspection data
        context['years_data'] = [{'val': str(y), 'selected': str(y) == year_filter} for y in sorted(list(all_years), reverse=True)]
        # Sort by area name (index 1 in tuple)
        sorted_areas = sorted(list(all_areas), key=lambda x: x[1])
        context['areas_data'] = [{'id': a[0], 'name': a[1], 'selected': str(a[0]) == str(area_filter)} for a in sorted_areas]
        
        return context

class InspectionCreateView(LoginRequiredMixin, CreateView):
    model = InspectionSchedule
    form_class = InspectionScheduleForm
    template_name = 'inspections/inspection_form.html'
    success_url = reverse_lazy('inspection_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        base = self.object
        
        # Robust year extraction
        try:
            target_year = int(form.cleaned_data.get('year'))
        except (ValueError, TypeError):
            target_year = base.scheduled_date.year
            
        current_date = base.scheduled_date
        
        # Robust frequency mapping
        freq_map = {
            'Mensual': 1,
            'Bimestral': 2,
            'Trimestral': 3,
            'Cuatrimestral': 4,
            'Semestral': 6,
            'Anual': 12
        }
        
        months_to_add = freq_map.get(base.frequency, 0)
        created_count = 0
        
        if months_to_add > 0:
            next_date = current_date + relativedelta(months=months_to_add)
            # Generate only within the target year
            while next_date.year == target_year:
                if not InspectionSchedule.objects.filter(
                    area=base.area,
                    inspection_type=base.inspection_type,
                    scheduled_date=next_date
                ).exists():
                    InspectionSchedule.objects.create(
                        year=target_year,
                        area=base.area,
                        inspection_type=base.inspection_type,
                        frequency=base.frequency,
                        scheduled_date=next_date,
                        responsible=base.responsible,
                        status='Programada',
                        observations=base.observations
                    )
                    created_count += 1
                next_date += relativedelta(months=months_to_add)

        if created_count > 0:
            messages.success(self.request, f'Se han generado {created_count} programaciones adicionales automáticas para {target_year}.')
        else:
            messages.success(self.request, f'Programación guardada exitosamente.')
            
        return response

class InspectionUpdateView(LoginRequiredMixin, UpdateView):
    model = InspectionSchedule
    form_class = InspectionUpdateForm
    template_name = 'inspections/inspection_form.html'
    success_url = reverse_lazy('inspection_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Programación actualizada correctamente')
        return response

class InspectionDeleteView(LoginRequiredMixin, DeleteView):
    model = InspectionSchedule
    template_name = 'inspections/inspection_confirm_delete.html'
    success_url = reverse_lazy('inspection_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Programación eliminada exitosamente')
        return super().delete(request, *args, **kwargs)

# Helper to link inspections
def link_to_schedule(request, obj):
    s_id = request.GET.get('schedule_item') or request.POST.get('schedule_item')
    if s_id:
        try:
            item = InspectionSchedule.objects.get(pk=s_id)
            obj.schedule_item = item
            obj.save()
            
            # Mark as done
            item.status = 'Realizada'
            item.save()
            
            # Generate next recurrence
            next_schedule = item.generate_next_schedule()
            if next_schedule:
                messages.info(request, f"📅 Nueva programación generada automáticamente para el {next_schedule.scheduled_date.strftime('%d/%m/%Y')}")
                
        except Exception as e:
            print(f"Error linking schedule: {e}")

# --- Mixin for Formsets ---
class FormsetMixin:
    formset_class = None
    initial_items = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items'] = self.formset_class(self.request.POST, instance=self.object)
        else:
            if not getattr(self, 'object', None) and self.initial_items:
                initial = [{'question': q} for q in self.initial_items]
                context['items'] = self.formset_class(instance=self.object, initial=initial)
                context['items'].extra = len(initial)
            else:
                context['items'] = self.formset_class(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            link_to_schedule(self.request, self.object)
            if items.is_valid():
                items.instance = self.object
                items.save()
            else:
                return self.form_invalid(form)
        return super().form_valid(form)

# 1. Extinguishers
class ExtinguisherListView(LoginRequiredMixin, ScheduledInspectionsMixin, ListView):
    model = ExtinguisherInspection
    template_name = 'inspections/extinguisher_list.html'
    context_object_name = 'inspections'
    inspection_module_type = 'extinguisher'  # For ScheduledInspectionsMixin

    def get_queryset(self):
        qs = super().get_queryset()
        from django.utils import timezone
        current_year = timezone.now().year
        return qs.filter(inspection_date__year=current_year)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        current_year = timezone.now().year
        
        # Filter scheduled inspections by year
        if 'scheduled_inspections' in context:
            context['scheduled_inspections'] = context['scheduled_inspections'].filter(scheduled_date__year=current_year)
            
        return context

class ExtinguisherCreateView(LoginRequiredMixin, FormsetMixin, CreateView):
    model = ExtinguisherInspection
    form_class = ExtinguisherInspectionForm
    formset_class = ExtinguisherItemFormSet
    template_name = 'inspections/extinguisher_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        schedule_item_id = self.request.GET.get('schedule_item')
        if schedule_item_id:
            try:
                from .models import InspectionSchedule
                obj = InspectionSchedule.objects.get(pk=schedule_item_id)
                initial['area'] = obj.area
            except InspectionSchedule.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.inspector = self.request.user
        
        schedule_item_id = self.request.GET.get('schedule_item')
        if schedule_item_id:
            try:
                from .models import InspectionSchedule
                obj = InspectionSchedule.objects.get(pk=schedule_item_id)
                form.instance.schedule_item = obj
                obj.status = 'Realizada'
                obj.save()
            except InspectionSchedule.DoesNotExist:
                pass

        response = super().form_valid(form)
        messages.success(self.request, f'Inspección de extintores guardada exitosamente para {form.instance.area}')
        return response
    
    def get_success_url(self):
        return reverse('extinguisher_detail', kwargs={'pk': self.object.pk})

class ExtinguisherUpdateView(LoginRequiredMixin, FormsetMixin, UpdateView):
    model = ExtinguisherInspection
    form_class = ExtinguisherInspectionForm
    formset_class = ExtinguisherItemFormSet
    template_name = 'inspections/extinguisher_form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de extintores actualizada correctamente')
        return response
    
    def get_success_url(self):
        return reverse('extinguisher_detail', kwargs={'pk': self.object.pk})

class ExtinguisherDetailView(LoginRequiredMixin, DetailView):
    model = ExtinguisherInspection; template_name = 'inspections/extinguisher_detail.html'

class ExtinguisherItemCreateView(LoginRequiredMixin, CreateView):
    model = ExtinguisherItem; form_class = ExtinguisherItemForm; template_name = 'inspections/extinguisher_item_form.html'
    def form_valid(self, form):
        insp = get_object_or_404(ExtinguisherInspection, pk=self.kwargs['pk'])
        form.instance.inspection = insp; form.save()
        if 'save_and_add' in self.request.POST: return redirect('extinguisher_item_create', pk=insp.pk)
        return redirect('extinguisher_detail', pk=insp.pk)

class ExtinguisherItemUpdateView(LoginRequiredMixin, UpdateView):
    model = ExtinguisherItem; form_class = ExtinguisherItemForm; template_name = 'inspections/extinguisher_item_form.html'
    def get_success_url(self): return reverse('extinguisher_detail', kwargs={'pk': self.object.inspection.pk})

# 2. First Aid
class FirstAidListView(LoginRequiredMixin, ScheduledInspectionsMixin, ListView):
    model = FirstAidInspection
    template_name = 'inspections/first_aid_list.html'
    context_object_name = 'inspections'
    inspection_module_type = 'first_aid'

class FirstAidCreateView(LoginRequiredMixin, FormsetMixin, CreateView):
    model = FirstAidInspection
    form_class = FirstAidInspectionForm
    formset_class = FirstAidItemFormSet
    template_name = 'inspections/first_aid_form.html'
    
    def form_valid(self, form):
        form.instance.inspector = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Inspección de botiquines guardada exitosamente para {form.instance.area}')
        return response
    
    def get_success_url(self):
        return reverse('first_aid_detail', kwargs={'pk': self.object.pk})

class FirstAidUpdateView(LoginRequiredMixin, FormsetMixin, UpdateView):
    model = FirstAidInspection
    form_class = FirstAidInspectionForm
    formset_class = FirstAidItemFormSet
    template_name = 'inspections/first_aid_form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de botiquines actualizada correctamente')
        return response
    
    def get_success_url(self):
        return reverse('first_aid_detail', kwargs={'pk': self.object.pk})

class FirstAidDetailView(LoginRequiredMixin, DetailView):
    model = FirstAidInspection; template_name = 'inspections/first_aid_detail.html'

class FirstAidItemCreateView(LoginRequiredMixin, CreateView):
    model = FirstAidItem; form_class = FirstAidItemForm; template_name = 'inspections/first_aid_item_form.html'
    def form_valid(self, form):
        insp = get_object_or_404(FirstAidInspection, pk=self.kwargs['pk'])
        form.instance.inspection = insp; form.save()
        if 'save_and_add' in self.request.POST: return redirect('first_aid_item_create', pk=insp.pk)
        return redirect('first_aid_detail', pk=insp.pk)

class FirstAidItemUpdateView(LoginRequiredMixin, UpdateView):
    model = FirstAidItem; form_class = FirstAidItemForm; template_name = 'inspections/first_aid_item_form.html'
    def get_success_url(self): return reverse('first_aid_detail', kwargs={'pk': self.object.inspection.pk})

# 3. Process
class ProcessListView(LoginRequiredMixin, ScheduledInspectionsMixin, ListView):
    model = ProcessInspection
    template_name = 'inspections/process_list.html'
    context_object_name = 'inspections'
    inspection_module_type = 'process'

class ProcessCreateView(LoginRequiredMixin, FormsetMixin, CreateView):
    model = ProcessInspection
    form_class = ProcessInspectionForm
    formset_class = ProcessItemFormSet
    template_name = 'inspections/process_form.html'
    
    initial_items = [
        "1. ¿Las áreas están señalizadas y la señalización se encuentra en buen estado?",
        "2. ¿Las paredes están limpias y el estado de la pintura es óptimo?",
        "3. ¿Los pisos están sin grietas y en buen estado de limpieza?",
        "4. ¿Existen equipos de control de incendios ubicados en lugar de fácil acceso?",
        "5. ¿Las áreas se encuentran en adecuado orden y aseo?",
        "6. ¿Las áreas cuentan con buena iluminación?",
        "7. ¿Las instalaciones eléctricas no presentan riesgos y tableros en buen estado?",
        "8. ¿Los recipientes de basura o residuos están señalizados?",
        "9. ¿Las áreas operativas están libres de materiales innecesarios?",
        "10. ¿Los lugares de acceso se encuentran libres de obstáculos?",
        "11. El personal que manipula las sustancias químicas conocen las hojas de seguridad (MSDS)?",
        "12. ¿Equipos de seguridad (extintores, camillas, botiquines) señalizados?",
        "13. ¿Recipientes de sustancias químicas rotulados e identificados?",
        "14. ¿Las máquinas y/o equipos del área se encuentran señalizadas?",
        "15. ¿Los sistemas de seguridad de la máquina funcionan y están señalizados?",
        "16. ¿La señalización de evacuación o de emergencia se encuentra en buen estado?"
    ]


    def form_valid(self, form):
        form.instance.inspector = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Inspección de procesos guardada exitosamente para {form.instance.area}')
        return response

    def get_success_url(self):
        return reverse('process_detail', kwargs={'pk': self.object.pk})

class ProcessUpdateView(LoginRequiredMixin, FormsetMixin, UpdateView):
    model = ProcessInspection
    form_class = ProcessInspectionForm
    formset_class = ProcessItemFormSet
    template_name = 'inspections/process_form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de procesos actualizada correctamente')
        return response
    
    def get_success_url(self):
        return reverse('process_detail', kwargs={'pk': self.object.pk})

class ProcessDetailView(LoginRequiredMixin, DetailView):
    model = ProcessInspection; template_name = 'inspections/process_detail.html'

# 4. Storage
class StorageListView(LoginRequiredMixin, ScheduledInspectionsMixin, ListView):
    model = StorageInspection
    template_name = 'inspections/storage_list.html'
    context_object_name = 'inspections'
    inspection_module_type = 'storage'

class StorageCreateView(LoginRequiredMixin, FormsetMixin, CreateView):
    model = StorageInspection
    form_class = StorageInspectionForm
    formset_class = StorageItemFormSet
    template_name = 'inspections/storage_form.html'
    
    initial_items = [
        "1. ¿Las áreas están claramente señalizadas y la señalización se encuentra en buen estado?",
        "2. ¿Las paredes están limpias y el estado de la pintura es óptimo?",
        "3. ¿Los pisos están sin grietas y en buen estado de limpieza?",
        "4. ¿Existen equipos de control de incendios ubicados en lugar de fácil acceso?",
        "5. ¿Las áreas se encuentran en adecuado orden y aseo?",
        "6. ¿Las áreas cuentan con buena iluminación?",
        "7. ¿Las instalaciones eléctricas no presentan riesgos y tableros en buen estado?",
        "8. ¿Los recipientes de basura o residuos están señalizados?",
        "9. ¿La distribución de estantes permite la circulación por los pasillos?",
        "10. ¿Los artículos de mayor peso se almacenan en la parte inferior?",
        "11. ¿El personal conoce las hojas de seguridad (MSDS)?",
        "12. ¿Equipos de seguridad (extintores, camillas, botiquines) señalizados?",
        "13. ¿Recipientes de sustancias químicas rotulados e identificados?",
        "14. ¿Equipos de transporte (estibadores) en buenas condiciones?",
        "15. ¿La señalización de evacuación o emergencia en buen estado?"
    ]

    def form_valid(self, form):
        form.instance.inspector = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Inspección de almacenamiento guardada exitosamente para {form.instance.area}')
        return response

    def get_success_url(self):
        return reverse('storage_detail', kwargs={'pk': self.object.pk})

class StorageUpdateView(LoginRequiredMixin, FormsetMixin, UpdateView):
    model = StorageInspection
    form_class = StorageInspectionForm
    formset_class = StorageItemFormSet
    template_name = 'inspections/storage_form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de almacenamiento actualizada correctamente')
        return response
    
    def get_success_url(self):
        return reverse('storage_detail', kwargs={'pk': self.object.pk})

class StorageDetailView(LoginRequiredMixin, DetailView):
    model = StorageInspection; template_name = 'inspections/storage_detail.html'

# 5. Forklift
class ForkliftListView(LoginRequiredMixin, ScheduledInspectionsMixin, ListView):
    model = ForkliftInspection
    template_name = 'inspections/forklift_list.html'
    context_object_name = 'inspections'
    inspection_module_type = 'forklift'

class ForkliftCreateView(LoginRequiredMixin, FormsetMixin, CreateView):
    model = ForkliftInspection
    form_class = ForkliftInspectionForm
    formset_class = ForkliftItemFormSet
    template_name = 'inspections/forklift_form.html'
    
    initial_items = [
        "1. Bateria sin Novedad (No sulfatada o cargada)",
        "2. Tanque de Gas (Golpes, Fugas)",
        "3. Agarradera trasera (Puntos de apoyo)",
        "4. Tres puntos de apoyo",
        "5. Escalón Antiderrapante",
        "6. Abulladuras, golpes, rayones, varios, etc...",
        "7. Control de velocidad velocidad regulada",
        "8. Acrilico protector del diplay en buen estado",
        "9. Limpieza del equipo",
        "10. Extintor (Buen estado, cargado, vigente)",
        "11. Espejos completos y en buen estado",
        "12. Llantas en buen estado (Delanteras, traseras)",
        "13. Pito Funcionando",
        "14. Asiento funcional (Respaldo y guias)",
        "15. Cinturon de seguridad en buen estado",
        "16. Etiqueta de altura maxima",
        "17. Etiqueta de peso máximo en buen estado",
        "18. Etiqueta de velocidad máxima",
        "19. Rejilla protectora superior en buen estado",
        "23. Luces funcionando (Frontales, traseras, reversa, torreta)",
        "25. Medidor nivel de combustible funcionando",
        "24. Alarma de reversa Funcionando",
        "25. Frenos en buen estado",
        "26. Dirección en buen estado (Sin juego)",
        "27. Funcionamiento del mastil adecuado",
        "28. Freno de mano en buen estado y funcionando",
        "29. Cadena de mastil en buen estado",
        "30. Presenta alguna fuga de aceite",
        "31. ¿El equipo es apto para su funcionamiento?"
    ]

    def form_valid(self, form):
        form.instance.inspector = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Inspección de montacargas guardada exitosamente - {form.instance.forklift_id}')
        return response

    def get_success_url(self):
        return reverse('forklift_detail', kwargs={'pk': self.object.pk})

class ForkliftUpdateView(LoginRequiredMixin, FormsetMixin, UpdateView):
    model = ForkliftInspection
    form_class = ForkliftInspectionForm
    formset_class = ForkliftItemFormSet
    template_name = 'inspections/forklift_form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Inspección de montacargas actualizada correctamente')
        return response
    
    def get_success_url(self):
        return reverse('forklift_detail', kwargs={'pk': self.object.pk})

class ForkliftDetailView(LoginRequiredMixin, DetailView):
    model = ForkliftInspection; template_name = 'inspections/forklift_detail.html'
