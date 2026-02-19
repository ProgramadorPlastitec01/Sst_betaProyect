from django.db import models
from django.core.exceptions import ValidationError

class Permission(models.Model):
    """
    Modelo de Permisos granulares del sistema.
    Cada permiso representa una acción específica en un módulo.
    """
    MODULE_CHOICES = [
        ('users', 'Usuarios'),
        ('inspections', 'Inspecciones'),
        ('schedule', 'Cronograma'),
        ('extinguisher', 'Extintores'),
        ('first_aid', 'Botiquines'),
        ('process', 'Procesos'),
        ('storage', 'Almacenamiento'),
        ('forklift', 'Montacargas'),
        ('roles', 'Roles'),
        ('reports', 'Reportes'),
    ]
    
    ACTION_CHOICES = [
        ('view', 'Ver módulo'),
        ('create', 'Registrar'),
        ('edit', 'Editar'),
        ('delete', 'Eliminar'),
        ('reset_password', 'Restablecer Contraseña'),
    ]
    
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='Módulo')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Acción')
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
