from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from .models import NotificationGroup, Notification
from users.models import CustomUser
from django import forms

class NotificationGroupForm(forms.ModelForm):
    class Meta:
        model = NotificationGroup
        fields = ['name', 'description', 'is_active', 'users']
        widgets = {
            'users': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class GroupListView(LoginRequiredMixin, ListView):
    model = NotificationGroup
    template_name = 'notifications/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = NotificationGroup
    form_class = NotificationGroupForm
    template_name = 'notifications/group_form.html'
    success_url = reverse_lazy('notification_group_list')

    def form_valid(self, form):
        messages.success(self.request, 'Grupo creado exitosamente.')
        return super().form_valid(form)

class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = NotificationGroup
    form_class = NotificationGroupForm
    template_name = 'notifications/group_form.html'
    success_url = reverse_lazy('notification_group_list')

    def form_valid(self, form):
        messages.success(self.request, 'Grupo actualizado exitosamente.')
        return super().form_valid(form)

class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = NotificationGroup
    template_name = 'notifications/group_confirm_delete.html'
    success_url = reverse_lazy('notification_group_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_system_default:
            messages.error(request, 'No se puede eliminar un grupo predeterminado del sistema.')
            return redirect('notification_group_list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Grupo eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('dashboard')
