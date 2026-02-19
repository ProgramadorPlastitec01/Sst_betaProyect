from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm, UserSignatureForm, AdminResetPasswordForm
from inspections.models import (
    InspectionSchedule, ExtinguisherInspection, FirstAidInspection,
    ProcessInspection, StorageInspection, ForkliftInspection
)
from datetime import date, timedelta

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('inactive'):
            messages.warning(request, 'Tu sesión fue cerrada por inactividad.')
        return super().get(request, *args, **kwargs)
        
    def get_success_url(self):
        return reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.get_full_name() or user.username}!')
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        today = date.today()
        
        # Get notification window from SystemConfig
        from system_config.models import SystemConfig
        notification_days = SystemConfig.get_value('dias_aviso_programacion', 7)
        try:
            notification_days = int(notification_days)
        except (ValueError, TypeError):
            notification_days = 7
            
        week_ahead = today + timedelta(days=notification_days)
        context['notification_days'] = notification_days
        
        # 1. Define modules and their patterns for InspectionSchedule
        inspection_modules = [
            {'key': 'extinguisher', 'patterns': ['extintor'], 'model': ExtinguisherInspection},
            {'key': 'first_aid', 'patterns': ['botiquin'], 'model': FirstAidInspection},
            {'key': 'process', 'patterns': ['proceso', 'instalacion'], 'model': ProcessInspection},
            {'key': 'storage', 'patterns': ['almacen', 'storage'], 'model': StorageInspection},
            {'key': 'forklift', 'patterns': ['montacarga'], 'model': ForkliftInspection},
        ]
        
        # 2. Check general permissions and build filter for schedules
        from django.db.models import Q
        schedule_filter = Q(pk__in=[]) # Default to none if no perms
        
        context['perm_schedule'] = user.has_perm_custom('schedule', 'view')
        context['perm_users'] = user.has_perm_custom('users', 'view')
        context['perm_roles'] = user.has_perm_custom('roles', 'view')
        
        allowed_keys = []
        active_findings = []

        for mod in inspection_modules:
            has_view = user.has_perm_custom(mod['key'], 'view')
            context[f'perm_{mod["key"]}'] = has_view
            
            if has_view:
                allowed_keys.append(mod['key'])
                # Add to schedule filter
                type_q = Q()
                for p in mod['patterns']:
                    type_q |= Q(inspection_type__icontains=p)
                schedule_filter |= type_q
                
                # Add to active findings
                # Inspections marked as 'Cerrada con Hallazgos' that are not fully resolved
                closed_with_findings = mod['model'].objects.filter(status='Cerrada con Hallazgos')
                for insp in closed_with_findings:
                    follow_up = insp.follow_ups.last()
                    if not follow_up or follow_up.status != 'Cerrada':
                        # Standardize name for dashboard display
                        labels = {
                            'extinguisher': 'Extintores',
                            'first_aid': 'Botiquines',
                            'process': 'Instalaciones de Proceso',
                            'storage': 'Almacenamiento',
                            'forklift': 'Montacargas'
                        }
                        insp.inspection_type = labels.get(mod['key'], 'Inspección')
                        active_findings.append(insp)

        # 3. Filter Schedules
        context['overdue_inspections'] = InspectionSchedule.objects.filter(
            schedule_filter,
            scheduled_date__lt=today
        ).exclude(status='Realizada').order_by('scheduled_date')
        
        context['upcoming_inspections'] = InspectionSchedule.objects.filter(
            schedule_filter,
            scheduled_date__gte=today,
            scheduled_date__lte=week_ahead
        ).exclude(status='Realizada').order_by('scheduled_date')

        context['active_findings'] = active_findings

        # 5. Counters for stat cards
        # Total Programadas = all InspectionSchedule items user can see
        total_scheduled_qs = InspectionSchedule.objects.filter(schedule_filter)
        context['total_scheduled'] = total_scheduled_qs.count()

        # Total Ejecutadas = consolidated count of actual inspection records
        inspection_models_map = [
            ('extinguisher', ExtinguisherInspection),
            ('first_aid', FirstAidInspection),
            ('process', ProcessInspection),
            ('storage', StorageInspection),
            ('forklift', ForkliftInspection),
        ]
        total_executed = 0
        for key, model_cls in inspection_models_map:
            if user.has_perm_custom(key, 'view'):
                qs_exec = model_cls.objects.all()
                if hasattr(model_cls, 'parent_inspection'):
                    qs_exec = qs_exec.filter(parent_inspection__isnull=True)
                total_executed += qs_exec.count()
        context['total_executed'] = total_executed

        # 6. User Notifications
        context['notifications'] = user.notifications.filter(is_read=False).order_by('-created_at')[:5]

        return context


class DashboardModalDataView(LoginRequiredMixin, View):
    """
    AJAX view that returns paginated + filtered data for Dashboard modals.
    table param: 'schedule' | 'executed'
    """

    INSPECTION_MODULES = [
        {'key': 'extinguisher', 'patterns': ['extintor'], 'model': ExtinguisherInspection,
         'label': 'Extintores', 'url': 'extinguisher_detail'},
        {'key': 'first_aid', 'patterns': ['botiquin'], 'model': FirstAidInspection,
         'label': 'Botiquines', 'url': 'first_aid_detail'},
        {'key': 'process', 'patterns': ['proceso', 'instalacion'], 'model': ProcessInspection,
         'label': 'Instalaciones de Proceso', 'url': 'process_detail'},
        {'key': 'storage', 'patterns': ['almacen', 'storage'], 'model': StorageInspection,
         'label': 'Almacenamiento', 'url': 'storage_detail'},
        {'key': 'forklift', 'patterns': ['montacarga'], 'model': ForkliftInspection,
         'label': 'Montacargas', 'url': 'forklift_detail'},
    ]

    def get(self, request, *args, **kwargs):
        user = request.user
        table = request.GET.get('table', 'schedule')  # 'schedule' | 'executed'
        page = int(request.GET.get('page', 1))
        per_page = 10

        # Shared filters
        q_search = request.GET.get('q', '').strip()
        f_date = request.GET.get('date', '').strip()
        f_type = request.GET.get('type', '').strip()
        f_status = request.GET.get('status', '').strip()

        # Build permission filter for schedule
        schedule_filter = Q(pk__in=[])
        allowed_mods = []
        for mod in self.INSPECTION_MODULES:
            if user.has_perm_custom(mod['key'], 'view'):
                allowed_mods.append(mod)
                t_q = Q()
                for p in mod['patterns']:
                    t_q |= Q(inspection_type__icontains=p)
                schedule_filter |= t_q

        if table == 'schedule':
            rows, total_count = self._get_schedule_data(
                schedule_filter, q_search, f_date, f_type, f_status, page, per_page
            )
        else:
            rows, total_count = self._get_executed_data(
                allowed_mods, q_search, f_date, f_type, f_status, page, per_page
            )

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        return JsonResponse({
            'rows': rows,
            'page': page,
            'total_pages': total_pages,
            'total_count': total_count,
        })

    def _get_schedule_data(self, schedule_filter, q, f_date, f_type, f_status, page, per_page):
        qs = InspectionSchedule.objects.filter(schedule_filter).select_related('area', 'responsible')

        if q:
            qs = qs.filter(
                Q(inspection_type__icontains=q) |
                Q(area__name__icontains=q) |
                Q(observations__icontains=q)
            )
        if f_date:
            qs = qs.filter(scheduled_date=f_date)
        if f_type:
            qs = qs.filter(inspection_type__icontains=f_type)
        if f_status:
            qs = qs.filter(status=f_status)

        qs = qs.order_by('-scheduled_date')
        total = qs.count()
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        rows = []
        for item in page_obj:
            rows.append({
                'id': item.pk,
                'date': item.scheduled_date.strftime('%d/%m/%Y') if item.scheduled_date else '',
                'type': item.inspection_type,
                'area': str(item.area) if item.area else '',
                'frequency': item.frequency,
                'responsible': item.responsible.get_full_name() if item.responsible else 'Equipo SST',
                'status': item.status,
                'observations': item.observations or '',
            })
        return rows, total

    def _get_executed_data(self, allowed_mods, q, f_date, f_type, f_status, page, per_page):
        all_items = []
        for mod in allowed_mods:
            model_cls = mod['model']
            label = mod['label']
            url_name = mod['url']

            # Type filter: skip module if not matching
            if f_type and f_type != label:
                continue

            qs = model_cls.objects.select_related('area', 'inspector').all()
            if hasattr(model_cls, 'parent_inspection'):
                qs = qs.filter(parent_inspection__isnull=True)

            if q:
                qs = qs.filter(
                    Q(area__name__icontains=q) |
                    Q(inspector__first_name__icontains=q) |
                    Q(inspector__last_name__icontains=q)
                )
            if f_date:
                qs = qs.filter(inspection_date=f_date)
            if f_status:
                qs = qs.filter(status=f_status)

            for insp in qs:
                status_val = getattr(insp, 'status', None) or getattr(insp, 'general_status', '')
                all_items.append({
                    'date_raw': insp.inspection_date,
                    'id': insp.pk,
                    'date': insp.inspection_date.strftime('%d/%m/%Y') if insp.inspection_date else '',
                    'type': label,
                    'area': str(insp.area) if insp.area else '',
                    'inspector': insp.inspector.get_full_name() if insp.inspector else 'N/A',
                    'status': status_val,
                    'detail_url': reverse(url_name, args=[insp.pk]),
                })

        # Sort by date descending
        all_items.sort(key=lambda x: x.get('date_raw') or date.min, reverse=True)
        # Remove sort key before pagination
        for item in all_items:
            item.pop('date_raw', None)

        total = len(all_items)
        start = (page - 1) * per_page
        end = start + per_page
        return all_items[start:end], total

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtering
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(document_number__icontains=search_query)
            )
            
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stats counters
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(is_active=True).count()
        context['inactive_users'] = CustomUser.objects.filter(is_active=False).count()
        
        # Pass filter values back to context
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        
        return context

class UserCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario {form.instance.username} creado exitosamente')
        return response

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario {form.instance.username} actualizado correctamente')
        return response

class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(self.request, f'Usuario {user.username} eliminado exitosamente')
        return super().delete(request, *args, **kwargs)

from django.contrib.auth.views import PasswordChangeView

class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signature_form'] = UserSignatureForm(instance=self.request.user)
        return context

class DigitalSignatureUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserSignatureForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Firma digital guardada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al guardar la firma')
        from django.shortcuts import redirect
        return redirect('user_profile')

class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('user_profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Contraseña actualizada correctamente')
        return super().form_valid(form)

class UserResetPasswordView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminResetPasswordForm
    template_name = 'users/user_reset_password.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if not request.user.has_perm_custom('users', 'reset_password'):
            messages.error(request, "No tienes permiso para restablecer contraseñas.")
            from django.shortcuts import redirect
            return redirect('user_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # AdminResetPasswordForm is not a ModelForm, so we remove 'instance'
        if 'instance' in kwargs:
            del kwargs['instance']
        return kwargs

    def form_valid(self, form):
        user = self.get_object()
        new_password = form.cleaned_data['new_password']
        user.set_password(new_password)
        user.save()
        messages.success(self.request, f'La contraseña de {user.get_full_name() or user.username} ha sido restablecida.')
        return super().form_valid(form)
