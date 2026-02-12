from django import forms
from .models import Role, Permission


class RoleForm(forms.ModelForm):
    """Formulario para crear/editar roles"""
    
    class Meta:
        model = Role
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del rol'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del rol'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nombre del Rol',
            'description': 'Descripción',
            'is_active': 'Activo',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Validar que no se modifique el nombre del rol Administrador
        if self.instance.pk and self.instance.name == 'Administrador' and name != 'Administrador':
            raise forms.ValidationError('No se puede cambiar el nombre del rol Administrador.')
        return name


class RolePermissionsForm(forms.Form):
    """Formulario para asignar permisos a un rol"""
    
    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)
        
        # Obtener todos los permisos activos agrupados por módulo
        permissions = Permission.objects.filter(is_active=True).order_by('module', 'action')
        
        # Agrupar permisos por módulo
        modules = {}
        for perm in permissions:
            if perm.module not in modules:
                modules[perm.module] = []
            modules[perm.module].append(perm)
        
        # Crear campos de checkbox para cada permiso
        for module_code, module_perms in modules.items():
            module_name = dict(Permission.MODULE_CHOICES).get(module_code, module_code)
            
            for perm in module_perms:
                field_name = f'perm_{perm.id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=perm.get_action_display(),
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                    initial=role.permissions.filter(id=perm.id).exists() if role else False
                )
                # Guardar metadata del permiso
                self.fields[field_name].permission = perm
                self.fields[field_name].module_name = module_name
    
    def get_permissions_by_module(self):
        """Retorna los campos agrupados por módulo para renderizado en template"""
        modules = {}
        for field_name, field in self.fields.items():
            if hasattr(field, 'permission'):
                module_name = field.module_name
                if module_name not in modules:
                    modules[module_name] = []
                modules[module_name].append({
                    'field_name': field_name,
                    'field': field,
                    'permission': field.permission
                })
        return modules
    
    def save(self, role):
        """Guarda los permisos seleccionados en el rol"""
        selected_permissions = []
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('perm_') and value:
                perm_id = int(field_name.split('_')[1])
                selected_permissions.append(perm_id)
        
        # Validar que Administrador tenga todos los permisos
        if role.name == 'Administrador':
            all_perms = Permission.objects.filter(is_active=True)
            role.permissions.set(all_perms)
        else:
            role.permissions.set(selected_permissions)
        
        return role
