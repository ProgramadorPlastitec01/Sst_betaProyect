from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    document_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.ForeignKey('roles.Role', on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='users', verbose_name='Rol')
    updated_at = models.DateTimeField(auto_now=True)
    
    digital_signature = models.TextField(blank=True, null=True, verbose_name="Firma Digital") # Base64 encoded image
    
    # We use email as the identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email
    
    def has_perm_custom(self, module, action):
        """
        Verifica si el usuario tiene un permiso específico a través de su rol.
        """
        # Acceso total para superusuarios y rol Administrador
        if self.is_superuser:
            return True
            
        if self.role and self.role.name == 'Administrador':
            return True
            
        if not self.role or not self.role.is_active:
            return False
            
        return self.role.has_permission(module, action)
    
    def get_role_name(self):
        """
        Retorna el nombre del rol del usuario.
        """
        return self.role.name if self.role else 'Sin Rol'
