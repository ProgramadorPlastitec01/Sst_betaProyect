from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Role, Permission, PERMISSION_MATRIX
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
    permission_required = ('roles', 'details')
    model = Role
    template_name = 'roles/role_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # IDs de permisos que tiene el rol
        role_perm_ids = set(self.object.permissions.values_list('id', flat=True))

        # Permisos activos indexados por codename
        active_perms = {
            p.codename: p
            for p in Permission.objects.filter(is_active=True)
        }

        module_labels = dict(Permission.MODULE_CHOICES)
        action_labels = dict(Permission.ACTION_CHOICES)

        from .models import ACTION_DISPLAY_ORDER

        # Columnas: todas las acciones que aparecen en la matriz, en orden
        all_actions = set()
        for actions in PERMISSION_MATRIX.values():
            all_actions.update(actions)
        columns = [a for a in ACTION_DISPLAY_ORDER if a in all_actions]
        column_labels = {a: action_labels.get(a, a.capitalize()) for a in columns}

        # Filas siguiendo el orden de PERMISSION_MATRIX
        rows = []
        for module_code, actions in PERMISSION_MATRIX.items():
            cells = {}
            for action_code in columns:
                if action_code in actions:
                    codename = f'{module_code}_{action_code}'
                    perm = active_perms.get(codename)
                    if perm:
                        cells[action_code] = {
                            'permission': perm,
                            'has_perm': perm.id in role_perm_ids,
                        }
                    else:
                        cells[action_code] = None  # Permiso no sincronizado aún
                else:
                    cells[action_code] = None  # No aplica a este módulo
            rows.append({
                'module_code': module_code,
                'module_name': module_labels.get(module_code, module_code.capitalize()),
                'cells': cells,
            })

        context['matrix_columns'] = columns
        context['matrix_column_labels'] = column_labels
        context['matrix_rows'] = rows
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
    if not request.user.has_perm_custom('roles', 'edit'):
        messages.error(request, 'No tienes permiso para modificar permisos de roles.')
        return redirect('role_list')
        
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
    
    # Construir la estructura de tabla-matriz para el template
    matrix_context = form.get_matrix_context()

    context = {
        'role': role,
        'form': form,
        'matrix_columns': matrix_context['columns'],
        'matrix_column_labels': matrix_context['column_labels'],
        'matrix_rows': matrix_context['rows'],
        'selected_permission_ids': selected_permission_ids,
    }
    return render(request, 'roles/role_permissions.html', context)


def toggle_role_status(request, pk):
    """Vista para activar/desactivar un rol"""
    if not request.user.has_perm_custom('roles', 'edit'):
         messages.error(request, 'No tienes permiso para modificar el estado de los roles.')
         return redirect('role_list')
         
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


# ─────────────────────────────────────────────────────────────────────────────
# SIMULACIÓN DE ROLES — Herramienta exclusiva para administradores
# Almacena el rol simulado únicamente en la sesión. Sin cambios en BD.
# ─────────────────────────────────────────────────────────────────────────────

from django.views import View


def _user_is_real_admin(user):
    """
    Verifica si el usuario es administrador real (superuser o rol Administrador).
    Usa el rol de BD directamente para evitar interferencia con simulaciones activas.
    """
    if user.is_superuser:
        return True
    real_role = getattr(user, '_real_role', None) or getattr(user, 'role', None)
    return real_role and real_role.name == 'Administrador'


class StartRoleSimulationView(LoginRequiredMixin, View):
    """
    POST: Activa la simulación de un rol para el administrador.
    Almacena el role_id en request.session['simulated_role_id'].
    No modifica ningún dato del usuario en base de datos.
    """

    def post(self, request, *args, **kwargs):
        # Solo administradores reales pueden activar simulación
        if not _user_is_real_admin(request.user):
            messages.error(request, 'No tienes permisos para usar la herramienta de simulación.')
            return redirect('role_list')

        role_id = request.POST.get('role_id')
        if not role_id:
            messages.error(request, 'Debe seleccionar un rol para simular.')
            return redirect('role_list')

        try:
            role = Role.objects.get(pk=role_id, is_active=True)
        except Role.DoesNotExist:
            messages.error(request, 'El rol seleccionado no existe o está inactivo.')
            return redirect('role_list')

        # Guardar en sesión (sin tocar la BD del usuario)
        request.session['simulated_role_id'] = role.pk
        messages.warning(
            request,
            f'Modo simulación activado. Ahora estás visualizando el sistema como: "{role.name}"'
        )
        return redirect('dashboard')


class StopRoleSimulationView(LoginRequiredMixin, View):
    """
    POST: Desactiva la simulación y restaura los permisos reales del administrador.
    Solo elimina la clave de sesión; no toca ningún dato en BD.
    """

    def post(self, request, *args, **kwargs):
        sim_role_id = request.session.pop('simulated_role_id', None)
        if sim_role_id:
            messages.success(request, 'Simulación finalizada. Has regresado a tus permisos reales.')
        return redirect('dashboard')

