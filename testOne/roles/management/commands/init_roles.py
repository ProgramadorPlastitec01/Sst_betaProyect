from django.core.management.base import BaseCommand
from roles.models import Permission, Role


class Command(BaseCommand):
    help = 'Inicializa permisos y roles del sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de permisos y roles...'))
        
        # 1. Crear todos los permisos
        self.create_permissions()
        
        # 2. Crear roles predeterminados
        self.create_roles()
        
        self.stdout.write(self.style.SUCCESS('[OK] Permisos y roles creados exitosamente!'))

    def create_permissions(self):
        """Crea todos los permisos del sistema"""
        self.stdout.write('Creando permisos...')
        
        modules = [
            ('users', 'Usuarios'),
            ('inspections', 'Inspecciones'),
            ('schedule', 'Cronograma'),
            ('extinguisher', 'Extintores'),
            ('first_aid', 'Botiquines'),
            ('process', 'Procesos'),
            ('storage', 'Almacenamiento'),
            ('forklift', 'Montacargas'),
            ('roles', 'Roles'),
        ]
        
        actions = [
            ('view', 'Ver módulo'),
            ('create', 'Registrar'),
            ('edit', 'Editar'),
            ('delete', 'Eliminar'),
        ]
        
        created_count = 0
        for module_code, module_name in modules:
            for action_code, action_name in actions:
                perm, created = Permission.objects.get_or_create(
                    module=module_code,
                    action=action_code,
                    defaults={
                        'codename': f'{module_code}_{action_code}',
                        'description': f'{action_name} en {module_name}',
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'  + Creado: {perm}')
        
        self.stdout.write(self.style.SUCCESS(f'  Total permisos creados: {created_count}'))

    def create_roles(self):
        """Crea los roles predeterminados del sistema"""
        self.stdout.write('Creando roles...')
        
        roles_data = [
            {
                'name': 'Administrador',
                'description': 'Acceso total al sistema',
                'is_system_role': True,
                'all_permissions': True
            },
            {
                'name': 'COPASST',
                'description': 'Comité Paritario de Seguridad y Salud en el Trabajo',
                'is_system_role': True,
                'permissions': ['inspections_view', 'schedule_view', 'extinguisher_view', 
                               'first_aid_view', 'process_view', 'storage_view', 'forklift_view']
            },
            {
                'name': 'Brigadista',
                'description': 'Miembro de la brigada de emergencias',
                'is_system_role': True,
                'permissions': ['extinguisher_view', 'first_aid_view', 'first_aid_edit']
            },
            {
                'name': 'Montacarguista',
                'description': 'Operador de montacargas',
                'is_system_role': True,
                'permissions': ['forklift_view', 'forklift_create', 'forklift_edit']
            },
            {
                'name': 'Almacenista',
                'description': 'Personal de almacén',
                'is_system_role': True,
                'permissions': ['storage_view', 'storage_create', 'storage_edit']
            },
            {
                'name': 'SST',
                'description': 'Seguridad y Salud en el Trabajo',
                'is_system_role': True,
                'permissions': ['inspections_view', 'inspections_create', 'inspections_edit',
                               'schedule_view', 'schedule_create', 'schedule_edit',
                               'extinguisher_view', 'extinguisher_create', 'extinguisher_edit',
                               'first_aid_view', 'first_aid_create', 'first_aid_edit',
                               'process_view', 'process_create', 'process_edit',
                               'storage_view', 'storage_create', 'storage_edit',
                               'forklift_view', 'forklift_create', 'forklift_edit']
            },
            {
                'name': 'Consulta',
                'description': 'Solo lectura de información',
                'is_system_role': True,
                'permissions': ['inspections_view', 'schedule_view', 'extinguisher_view',
                               'first_aid_view', 'process_view', 'storage_view', 'forklift_view']
            },
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system_role': role_data['is_system_role'],
                    'is_active': True
                }
            )
            
            if created or role.name == 'Administrador':
                # Asignar permisos
                if role_data.get('all_permissions'):
                    # Administrador tiene todos los permisos
                    all_perms = Permission.objects.filter(is_active=True)
                    role.permissions.set(all_perms)
                    self.stdout.write(f'  + Rol "{role.name}" creado con TODOS los permisos')
                else:
                    # Asignar permisos específicos
                    perms = Permission.objects.filter(
                        codename__in=role_data.get('permissions', []),
                        is_active=True
                    )
                    role.permissions.set(perms)
                    self.stdout.write(f'  + Rol "{role.name}" creado con {perms.count()} permisos')
            else:
                self.stdout.write(f'  - Rol "{role.name}" ya existe')
        
        self.stdout.write(self.style.SUCCESS(f'  Total roles: {Role.objects.count()}'))
