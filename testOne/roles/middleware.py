"""
roles/middleware.py
-------------------
Middleware de simulación de roles.

En cada request verifica si hay un rol simulado almacenado en la sesión.
Si está activo, parchea temporalmente `request.user.has_perm_custom()` en
memoria para que toda la lógica RBAC existente (mixin, template tags, sidebar)
funcione con los permisos del rol simulado — sin modificar ningún dato en BD.

Requisitos para activar la simulación:
  - El usuario real debe ser superusuario o tener rol 'Administrador'.
  - El rol simulado debe existir y estar activo.

El parche es por-request (thread-safe) y desaparece al terminar el ciclo.
"""


class RoleSimulationMiddleware:
    SESSION_KEY = 'simulated_role_id'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo actuar sobre usuarios autenticados
        if request.user.is_authenticated:
            simulated_role_id = request.session.get(self.SESSION_KEY)

            if simulated_role_id:
                self._apply_simulation(request, simulated_role_id)

        response = self.get_response(request)
        return response

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _is_real_admin(self, user):
        """Verifica si el usuario REAL (sin simulación) es administrador."""
        # Usamos el atributo de BD directamente, no has_perm_custom, porque
        # este middleware puede haber sido ya parcheado en requests previos.
        if user.is_superuser:
            return True
        # Accedemos al rol real a través del FK (no del parche en memoria)
        real_role = getattr(user, '_real_role', None) or getattr(user, 'role', None)
        return real_role and real_role.name == 'Administrador'

    def _apply_simulation(self, request, simulated_role_id):
        """
        Parchea has_perm_custom() del usuario con la lógica del rol simulado.
        Si el rol ya no existe o el usuario perdió privilegios, cancela la sesión.
        """
        from .models import Role

        # Verificar que el usuario real sigue siendo administrador
        if not self._is_real_admin(request.user):
            request.session.pop(self.SESSION_KEY, None)
            return

        try:
            sim_role = Role.objects.get(pk=simulated_role_id, is_active=True)
        except Role.DoesNotExist:
            # El rol fue eliminado o desactivado; cancelar simulación
            request.session.pop(self.SESSION_KEY, None)
            return

        # Guardar referencia al rol real antes de parchear
        request.user._real_role = getattr(request.user, 'role', None)

        # Adjuntar el rol simulado al usuario para que templates y vistas
        # puedan detectar el modo de simulación
        request.user._simulated_role = sim_role

        # ── Parche en memoria de has_perm_custom ──────────────────────
        # Capturamos sim_role en el closure para que no cambie entre requests
        def simulated_has_perm(module, action):
            """
            Sustituye has_perm_custom() durante la simulación.

            El rol 'Administrador' tiene acceso total; cualquier otro rol
            consulta sus permisos asignados en BD.
            """
            if sim_role.name == 'Administrador':
                return True
            if not sim_role.is_active:
                return False
            return sim_role.has_permission(module, action)

        # Monkey-patch: solo afecta a esta instancia de usuario en este request
        request.user.has_perm_custom = simulated_has_perm
