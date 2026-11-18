from django import forms
from .models import Role, Permission, PERMISSION_MATRIX, ACTION_DISPLAY_ORDER


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
    """
    Formulario para asignar permisos a un rol.

    Genera un campo BooleanField por cada permiso activo en la matriz.
    La estructura interna refleja PERMISSION_MATRIX — es la fuente de verdad
    para decidir qué acciones aplican a cada módulo.
    """

    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)

        # IDs de permisos ya asignados al rol
        role_perm_ids = set(role.permissions.values_list('id', flat=True)) if role else set()

        # Cargar solo permisos activos en BD, indexados por codename
        active_perms = {
            p.codename: p
            for p in Permission.objects.filter(is_active=True)
        }

        module_labels = dict(Permission.MODULE_CHOICES)
        action_labels = dict(Permission.ACTION_CHOICES)

        # Crear campos siguiendo el orden de la matriz
        for module_code, actions in PERMISSION_MATRIX.items():
            for action_code in actions:
                codename = f'{module_code}_{action_code}'
                perm = active_perms.get(codename)
                if not perm:
                    continue  # Permiso aún no en BD (no debería pasar después del sync)

                field_name = f'perm_{perm.id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=action_labels.get(action_code, action_code.capitalize()),
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                    initial=perm.id in role_perm_ids,
                )
                # Metadata para renderizado en template
                self.fields[field_name].permission = perm
                self.fields[field_name].module_code = module_code
                self.fields[field_name].module_name = module_labels.get(module_code, module_code.capitalize())
                self.fields[field_name].action_code = action_code

    def get_matrix_context(self):
        """
        Retorna una estructura lista para renderizar la tabla-matriz:

        {
          'columns': ['view', 'create', 'edit', 'delete', 'details', 'reset_password', 'gestionar_movimientos'],
          'column_labels': {'view': 'Acceso', 'create': 'Registrar', ...},
          'rows': [
            {
              'module_code': 'users',
              'module_name': 'Usuarios',
              'cells': {
                'view':   {'field_name': 'perm_1', 'field': <BooleanField>, 'permission': <Permission>},
                'create': {'field_name': 'perm_2', ...},
                'edit':   None,  # Acción no aplica a este módulo
                ...
              }
            },
            ...
          ]
        }
        """
        action_labels = dict(Permission.ACTION_CHOICES)
        module_labels = dict(Permission.MODULE_CHOICES)

        # Determinar las columnas: unión de todas las acciones, en orden definido
        all_actions_in_matrix = set()
        for actions in PERMISSION_MATRIX.values():
            all_actions_in_matrix.update(actions)

        columns = [a for a in ACTION_DISPLAY_ORDER if a in all_actions_in_matrix]
        column_labels = {a: action_labels.get(a, a.capitalize()) for a in columns}

        # Indexar campos por módulo y acción
        field_index = {}  # (module_code, action_code) -> {field_name, field, permission, has_perm}
        for field_name, field in self.fields.items():
            if hasattr(field, 'permission'):
                key = (field.module_code, field.action_code)
                # has_perm: true if the checkbox should be pre-checked
                # field.initial holds the boolean from __init__
                has_perm = bool(field.initial)
                field_index[key] = {
                    'field_name': field_name,
                    'field': field,
                    'permission': field.permission,
                    'has_perm': has_perm,
                }

        # Construir filas según el orden de PERMISSION_MATRIX
        rows = []
        for module_code, actions in PERMISSION_MATRIX.items():
            cells = {}
            for action_code in columns:
                if action_code in actions:
                    cells[action_code] = field_index.get((module_code, action_code))
                else:
                    cells[action_code] = None  # No aplica
            rows.append({
                'module_code': module_code,
                'module_name': module_labels.get(module_code, module_code.capitalize()),
                'actions': actions,
                'cells': cells,
            })

        return {
            'columns': columns,
            'column_labels': column_labels,
            'rows': rows,
        }

    def save(self, role):
        """Guarda los permisos seleccionados en el rol"""
        if role.name == 'Administrador':
            # El Administrador siempre tiene todos los permisos activos
            role.permissions.set(Permission.objects.filter(is_active=True))
        else:
            selected_ids = []
            for field_name, value in self.cleaned_data.items():
                if field_name.startswith('perm_') and value:
                    perm_id = int(field_name.split('_')[1])
                    selected_ids.append(perm_id)
            role.permissions.set(selected_ids)
        return role
