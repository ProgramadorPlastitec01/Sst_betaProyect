from django.core.management.base import BaseCommand
from roles.models import Permission

class Command(BaseCommand):
    help = 'Inicializa los permisos del sistema'

    def handle(self, *args, **options):
        
        # Estructura base de permisos por módulo según requerimiento:
        # 1. Acceso (view)
        # 2. Registrar (create)
        # 3. Modificar (edit) 
        # 4. Eliminar (delete)
        # 5. Consulta (details)
        
        standard_actions = [
            ('view', 'Acceso al módulo'),
            ('create', 'Registrar'),
            ('edit', 'Modificar'),
            ('delete', 'Eliminar'),
            ('details', 'Consulta'),
        ]
        
        modules = dict(Permission.MODULE_CHOICES)
        
        permissions_data = []
        
        # Generar automáticamente los 5 permisos estándar para cada módulo
        for mod_code, mod_name in modules.items():
            for act_code, act_label in standard_actions:
                permissions_data.append({
                    'module': mod_code,
                    'action': act_code,
                    'description': f'{act_label} en {mod_name}'
                })
        
        # Agregar permisos especiales existentes para no romper funcionalidad
        special_permissions = [
            {'module': 'users', 'action': 'reset_password', 'description': 'Restablecer Contraseña en Usuarios'},
            {'module': 'assets', 'action': 'gestionar_movimientos', 'description': 'Gestionar Movimientos en Gestión de Activos'},
        ]
        
        permissions_data.extend(special_permissions)
        
        self.stdout.write(self.style.SUCCESS('\n=== Inicializando Permisos ===\n'))
        
        created_count = 0
        existing_count = 0
        updated_count = 0
        
        for perm_data in permissions_data:
            codename = f"{perm_data['module']}_{perm_data['action']}"
            
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'module': perm_data['module'],
                    'action': perm_data['action'],
                    'description': perm_data['description'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [OK] {perm.description}'))
            else:
                # Update description if it changed (to match new naming convention)
                if perm.description != perm_data['description']:
                    perm.description = perm_data['description']
                    perm.module = perm_data['module']
                    perm.action = perm_data['action']
                    perm.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  [UPDATED] {perm.description}'))
                else:
                    existing_count += 1
                    self.stdout.write(f'  [--] {perm.description}')
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'Permisos creados: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Permisos actualizados: {updated_count}'))
        self.stdout.write(f'Permisos existentes: {existing_count}')
        self.stdout.write(self.style.SUCCESS(f'Total de permisos: {Permission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nAhora ejecuta: python manage.py init_roles'))
