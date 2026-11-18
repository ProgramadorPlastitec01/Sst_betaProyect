from django.db import models
from django.core.exceptions import ValidationError

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE ÚNICA DE VERDAD — Matriz de permisos reales del sistema
#
# Define exactamente qué acciones existen para cada módulo.
# - Cada entrada aquí DEBE tener una vista/acción real que la consuma.
# - Cada vista/acción real DEBE aparecer aquí.
# - Usar esta constante para sync de BD, UI y validaciones.
# ─────────────────────────────────────────────────────────────────────────────
PERMISSION_MATRIX = {
    # Gestión de usuarios del sistema
    'users': ['view', 'create', 'edit', 'delete', 'reset_password'],

    # Gestión de roles y permisos
    'roles': ['view', 'create', 'edit', 'delete', 'details'],

    # Cronograma anual de inspecciones
    'schedule': ['view', 'create', 'edit', 'delete'],

    # Módulos de inspección — 'delete' = baja lógica (soft-delete), trazabilidad preservada
    'extinguisher': ['view', 'create', 'edit', 'delete', 'details'],
    'first_aid':    ['view', 'create', 'edit', 'delete', 'details'],
    'process':      ['view', 'create', 'edit', 'delete', 'details'],
    'storage':      ['view', 'create', 'edit', 'delete', 'details'],
    'forklift':     ['view', 'create', 'edit', 'delete', 'details'],

    # Inventario de activos físicos
    'assets': ['view', 'details', 'create', 'edit', 'delete', 'gestionar_movimientos'],

    # Reportes consolidados (solo consulta + exportación)
    'reports': ['view'],

    # Visualización y posicionamiento de activos en planos SVG
    'planos': ['view', 'edit'],
}

# Orden de presentación de las acciones en la UI de permisos
ACTION_DISPLAY_ORDER = ['view', 'create', 'edit', 'delete', 'details', 'reset_password', 'gestionar_movimientos']

class Permission(models.Model):
    """
    Modelo de Permisos granulares del sistema.
    Cada permiso representa una acción específica en un módulo.
    """
    MODULE_CHOICES = [
        ('users', 'Usuarios'),
        ('schedule', 'Cronograma'),
        ('extinguisher', 'Extintores'),
        ('first_aid', 'Botiquines'),
        ('process', 'Procesos'),
        ('storage', 'Almacenamiento'),
        ('forklift', 'Montacargas'),
        ('assets', 'Gestión de Activos'),
        ('roles', 'Roles'),
        ('reports', 'Reportes'),
        ('planos', 'Planos'),
    ]
    
    ACTION_CHOICES = [
        ('view', 'Acceso al módulo'),
        ('create', 'Registrar'),
        ('edit', 'Modificar'),
        ('delete', 'Eliminar'),
        ('details', 'Consulta'),
        ('reset_password', 'Restablecer Contraseña'),
        ('gestionar_movimientos', 'Gestionar Movimientos'),
    ]
    
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='Módulo')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name='Acción')
    codename = models.CharField(max_length=100, unique=True, verbose_name='Código')
    description = models.CharField(max_length=255, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['module', 'action']
        unique_together = ['module', 'action']
    
    def __str__(self):
        return f"{self.get_module_display()} - {self.get_action_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generar codename si no existe
        if not self.codename:
            self.codename = f"{self.module}_{self.action}"
        if not self.description:
            self.description = f"{self.get_action_display()} en {self.get_module_display()}"
        super().save(*args, **kwargs)


class Role(models.Model):
    """
    Modelo de Roles del sistema.
    Un rol agrupa permisos y se asigna a usuarios.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre del Rol')
    description = models.TextField(blank=True, verbose_name='Descripción')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles', verbose_name='Permisos')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_system_role = models.BooleanField(default=False, verbose_name='Rol del Sistema')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        # Validar que el rol Administrador siempre tenga todos los permisos
        if self.name == 'Administrador' and self.pk:
            all_permissions = Permission.objects.filter(is_active=True)
            current_permissions = self.permissions.all()
            if current_permissions.count() < all_permissions.count():
                raise ValidationError('El rol Administrador debe tener todos los permisos activos.')
    
    def has_permission(self, module, action):
        """
        Verifica si el rol tiene un permiso específico.
        """
        if not self.is_active:
            return False
        
        return self.permissions.filter(
            module=module,
            action=action,
            is_active=True
        ).exists()
    
    def get_permissions_by_module(self):
        """
        Retorna permisos agrupados por módulo.
        """
        permissions_dict = {}
        for perm in self.permissions.filter(is_active=True):
            if perm.module not in permissions_dict:
                permissions_dict[perm.module] = []
            permissions_dict[perm.module].append(perm)
        return permissions_dict
