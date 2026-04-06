from django.core.management.base import BaseCommand
from roles.models import Permission

class Command(BaseCommand):
    help = 'Inicializa los permisos del sistema'

    def handle(self, *args, **options):
        
        # Definición precisa de permisos por módulo según funcionalidad real
        module_permissions = {
            'users': ['view', 'create', 'edit', 'delete', 'details', 'reset_password'],
            'schedule': ['view', 'create', 'edit', 'delete', 'details'],
            'extinguisher': ['view', 'create', 'edit', 'details'],
            'first_aid': ['view', 'create', 'edit', 'details'],
            'process': ['view', 'create', 'edit', 'details'],
            'storage': ['view', 'create', 'edit', 'details'],
            'forklift': ['view', 'create', 'edit', 'details'],
            'assets': ['view', 'create', 'edit', 'delete', 'details', 'gestionar_movimientos'],
            'roles': ['view', 'create', 'edit', 'delete', 'details'],
            'reports': ['view'],
            'planos': ['view', 'create', 'edit', 'delete', 'details'],
        }
        
        action_labels = dict(Permission.ACTION_CHOICES)
        modules_labels = dict(Permission.MODULE_CHOICES)
        
        permissions_data = []
        
        for mod_code, actions in module_permissions.items():
            mod_label = modules_labels.get(mod_code, mod_code.capitalize())
            for act_code in actions:
                act_label = action_labels.get(act_code, act_code.capitalize())
                permissions_data.append({
                    'module': mod_code,
                    'action': act_code,
                    'description': f'{act_label} en {mod_label}'
                })
        
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
        
        # 4. Limpiar permisos obsoletos (Crucial para eliminar los permisos fantasma)
        current_codenames = [f"{p['module']}_{p['action']}" for p in permissions_data]
        deleted_count, _ = Permission.objects.exclude(codename__in=current_codenames).delete()
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'Permisos creados: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Permisos actualizados: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Permisos obsoletos eliminados: {deleted_count}'))
        self.stdout.write(f'Permisos mantenos/existentes: {existing_count}')
        self.stdout.write(self.style.SUCCESS(f'Total de permisos activos: {Permission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nAhora ejecuta: python manage.py init_roles'))
