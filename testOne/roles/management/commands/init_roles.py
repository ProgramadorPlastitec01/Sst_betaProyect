from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from roles.models import Role, Permission

class Command(BaseCommand):
    help = 'Inicializa los roles del sistema y asigna permisos al administrador'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Definir roles con sus descripciones
        roles_data = [
            {
                'name': 'Administrador',
                'description': 'Acceso total al sistema, gestión de usuarios, roles y configuraciones',
                'permissions': 'all'  # Todos los permisos
            },
            {
                'name': 'Equipo SST',
                'description': 'Equipo de Seguridad y Salud en el Trabajo, gestión de inspecciones y cronogramas',
                'permissions': ['view', 'create', 'edit']  # Ver, crear y editar inspecciones
            },
            {
                'name': 'Almacenista',
                'description': 'Responsable de inspecciones de almacenamiento y control de inventarios',
                'permissions': ['view', 'create', 'edit']
            },
            {
                'name': 'Brigadista',
                'description': 'Responsable de inspecciones de extintores y botiquines de primeros auxilios',
                'permissions': ['view', 'create', 'edit']
            },
            {
                'name': 'Montacarguista',
                'description': 'Operador de montacargas, responsable de inspecciones de equipos',
                'permissions': ['view', 'create']  # Solo ver y crear sus inspecciones
            },
            {
                'name': 'Consulta',
                'description': 'Acceso de solo lectura para consultar inspecciones y reportes',
                'permissions': ['view']  # Solo lectura
            },
        ]
        
        self.stdout.write(self.style.SUCCESS('\n=== Inicializando Roles ===\n'))
        
        created_roles = []
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            
            if created:
                created_roles.append(role)
                self.stdout.write(self.style.SUCCESS(f'  [OK] Rol creado: {role.name}'))
            else:
                self.stdout.write(f'  [--] Rol existente: {role.name}')
            
            # Asignar permisos
            if role_data['permissions'] == 'all':
                # Administrador: todos los permisos
                all_permissions = Permission.objects.all()
                role.permissions.set(all_permissions)
                self.stdout.write(f'      -> {all_permissions.count()} permisos asignados (TODOS)')
            else:
                # Otros roles: permisos específicos
                permissions_to_assign = []
                for perm_code in role_data['permissions']:
                    perms = Permission.objects.filter(codename__icontains=perm_code)
                    permissions_to_assign.extend(perms)
                
                role.permissions.set(permissions_to_assign)
                self.stdout.write(f'      -> {len(permissions_to_assign)} permisos asignados')
        
        # Asignar rol de Administrador al usuario datamaster
        self.stdout.write(self.style.SUCCESS('\n=== Asignando Rol a Usuario ===\n'))
        
        try:
            admin_user = User.objects.get(username='datamaster')
            admin_role = Role.objects.get(name='Administrador')
            
            admin_user.role = admin_role
            admin_user.save()
            
            self.stdout.write(self.style.SUCCESS(f'  [OK] Usuario "{admin_user.username}" asignado al rol "{admin_role.name}"'))
            self.stdout.write(f'      -> Email: {admin_user.email}')
            self.stdout.write(f'      -> Staff: {admin_user.is_staff}')
            self.stdout.write(f'      -> Superuser: {admin_user.is_superuser}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('  [!!] Usuario "datamaster" no encontrado'))
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('  [ERROR] Rol "Administrador" no encontrado'))
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'Roles creados: {len(created_roles)}'))
        self.stdout.write(f'Roles existentes: {Role.objects.count() - len(created_roles)}')
        self.stdout.write(self.style.SUCCESS(f'Total de roles: {Role.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total de permisos: {Permission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\n¡Inicialización completada!'))
