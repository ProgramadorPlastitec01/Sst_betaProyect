from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm
from inspections.models import InspectionSchedule
from datetime import date, timedelta

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.get_full_name() or user.username}!')
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = date.today()
        week_ahead = today + timedelta(days=7)
        
        # Overdue: Date < Today AND Status != 'Realizada'
        context['overdue_inspections'] = InspectionSchedule.objects.filter(
            scheduled_date__lt=today
        ).exclude(status='Realizada').order_by('scheduled_date')
        
        # Upcoming: Today <= Date <= Week Ahead AND Status != 'Realizada'
        context['upcoming_inspections'] = InspectionSchedule.objects.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=week_ahead
        ).exclude(status='Realizada').order_by('scheduled_date')
        
        return context

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

class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('user_profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Contraseña actualizada correctamente')
        return super().form_valid(form)
