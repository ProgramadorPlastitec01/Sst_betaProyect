from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Role, Permission
from .forms import RoleForm, RolePermissionsForm
from .mixins import RolePermissionRequiredMixin


class RoleListView(LoginRequiredMixin, RolePermissionRequiredMixin, ListView):
    """Vista para listar todos los roles"""
    permission_required = ('roles', 'view')
    model = Role
    template_name = 'roles/role_list.html'
    context_object_name = 'roles'
    
    def get_queryset(self):
        queryset = Role.objects.all().prefetch_related('permissions', 'users')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Stats counters
        context['total_roles'] = Role.objects.count()
        context['system_roles'] = Role.objects.filter(is_system_role=True).count()
        context['active_roles'] = Role.objects.filter(is_active=True).count()
        
        # Pass filter value back
        context['search'] = self.request.GET.get('search', '')
        
        return context


class RoleCreateView(LoginRequiredMixin, RolePermissionRequiredMixin, CreateView):
    """Vista para crear un nuevo rol"""
    permission_required = ('roles', 'create')
    model = Role
    form_class = RoleForm
    template_name = 'roles/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Rol "{form.instance.name}" creado exitosamente')
        return response


class RoleUpdateView(LoginRequiredMixin, RolePermissionRequiredMixin, UpdateView):
    """Vista para editar un rol existente"""
    permission_required = ('roles', 'edit')
    model = Role
    form_class = RoleForm
    template_name = 'roles/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Rol "{form.instance.name}" actualizado correctamente')
        return response


class RoleDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, DetailView):
    """Vista para ver detalles de un rol"""
    permission_required = ('roles', 'view')
    model = Role
    template_name = 'roles/role_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los permisos definidos en el sistema
        all_permissions = Permission.objects.all().order_by('module', 'action')
        
        # Obtener IDs de permisos que tiene el rol
        role_perm_ids = set(self.object.permissions.values_list('id', flat=True))
        
        # Agrupar por módulo para visualizar
        # Estructura: {'users': {'name': 'Usuarios', 'perms': [{'obj': p, 'has': True}, ...]}, ...}
        permissions_matrix = {}
        
        # Usar MODULE_CHOICES para iterar en orden y obtener nombres legibles
        module_dict = dict(Permission.MODULE_CHOICES)
        
        for module_key, module_name in Permission.MODULE_CHOICES:
            # Filtrar permisos de este módulo
            module_perms = [p for p in all_permissions if p.module == module_key]
            
            if module_perms:
                perms_list = []
                for p in module_perms:
                    perms_list.append({
                        'permission': p,
                        'has_perm': p.id in role_perm_ids
                    })
                
                permissions_matrix[module_key] = {
                    'name': module_name,
                    'vals': perms_list
                }
        
        context['permissions_matrix'] = permissions_matrix
        return context


class RoleDeleteView(LoginRequiredMixin, RolePermissionRequiredMixin, DeleteView):
    """Vista para eliminar un rol"""
    permission_required = ('roles', 'delete')
    model = Role
    template_name = 'roles/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')
    
    def delete(self, request, *args, **kwargs):
        role = self.get_object()
        
        # Validar que no se elimine el rol Administrador
        if role.name == 'Administrador':
            messages.error(request, 'No se puede eliminar el rol Administrador.')
            return redirect('role_list')
        
        # Validar que no haya usuarios asignados
        if role.users.exists():
            messages.error(
                request,
                f'No se puede eliminar el rol "{role.name}" porque tiene {role.users.count()} usuario(s) asignado(s).'
            )
            return redirect('role_list')
        
        messages.success(request, f'Rol "{role.name}" eliminado exitosamente')
        return super().delete(request, *args, **kwargs)


def role_permissions_view(request, pk):
    """Vista para asignar permisos a un rol"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        form = RolePermissionsForm(request.POST, role=role)
        if form.is_valid():
            form.save(role)
            messages.success(request, f'Permisos del rol "{role.name}" actualizados correctamente')
            return redirect('role_detail', pk=role.pk)
    else:
        form = RolePermissionsForm(role=role)
    
    # Obtener IDs de permisos seleccionados para el rol
    selected_permission_ids = set(role.permissions.values_list('id', flat=True))
    
    context = {
        'role': role,
        'form': form,
        'permissions_by_module': form.get_permissions_by_module(),
        'selected_permission_ids': selected_permission_ids,
    }
    return render(request, 'roles/role_permissions.html', context)


def toggle_role_status(request, pk):
    """Vista para activar/desactivar un rol"""
    role = get_object_or_404(Role, pk=pk)
    
    # Validar que no se desactive el rol Administrador
    if role.name == 'Administrador' and role.is_active:
        messages.error(request, 'No se puede desactivar el rol Administrador.')
        return redirect('role_list')
    
    role.is_active = not role.is_active
    role.save()
    
    status = 'activado' if role.is_active else 'desactivado'
    messages.success(request, f'Rol "{role.name}" {status} correctamente')
    return redirect('role_list')
