from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class RolePermissionRequiredMixin(AccessMixin):
    """
    Mixin para requerir un permiso específico de rol.
    Verifica si el usuario tiene el permiso especificado en permission_required.
    permission_required debe ser una tupla ('modulo', 'accion').
    """
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if not self.has_permission():
            messages.error(request, 'No tienes permiso para realizar esta acción o acceder a esta sección.')
            
            # Intentar volver a la página anterior
            referer = request.META.get('HTTP_REFERER')
            if referer and referer != request.build_absolute_uri():
                return redirect(referer)
                
            # Fallback al dashboard
            return redirect('dashboard')
            
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        if self.permission_required:
            user = self.request.user
            # Verificar si el usuario tiene el método custom
            if hasattr(user, 'has_perm_custom'):
                if isinstance(self.permission_required, (list, tuple)) and len(self.permission_required) == 2:
                    module, action = self.permission_required
                    return user.has_perm_custom(module, action)
        return True
