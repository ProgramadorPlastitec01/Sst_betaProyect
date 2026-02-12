from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

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

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'

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
