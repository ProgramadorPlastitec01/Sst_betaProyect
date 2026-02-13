from django.core.management.base import BaseCommand
from roles.models import Permission

class Command(BaseCommand):
    help = 'Inicializa los permisos del sistema'

    def handle(self, *args, **options):
        
        # Definir todos los permisos del sistema
        permissions_data = [
            # Usuarios
            {'module': 'users', 'action': 'view', 'description': 'Ver listado de usuarios'},
            {'module': 'users', 'action': 'create', 'description': 'Crear nuevos usuarios'},
            {'module': 'users', 'action': 'edit', 'description': 'Editar usuarios existentes'},
            {'module': 'users', 'action': 'delete', 'description': 'Eliminar usuarios'},
            
            # Roles
            {'module': 'roles', 'action': 'view', 'description': 'Ver listado de roles'},
            {'module': 'roles', 'action': 'create', 'description': 'Crear nuevos roles'},
            {'module': 'roles', 'action': 'edit', 'description': 'Editar roles y permisos'},
            {'module': 'roles', 'action': 'delete', 'description': 'Eliminar roles'},
            
            # Cronograma
            {'module': 'schedule', 'action': 'view', 'description': 'Ver cronograma anual'},
            {'module': 'schedule', 'action': 'create', 'description': 'Programar nuevas inspecciones'},
            {'module': 'schedule', 'action': 'edit', 'description': 'Editar programaciones'},
            {'module': 'schedule', 'action': 'delete', 'description': 'Eliminar programaciones'},
            
            # Extintores
            {'module': 'extinguisher', 'action': 'view', 'description': 'Ver inspecciones de extintores'},
            {'module': 'extinguisher', 'action': 'create', 'description': 'Registrar inspecciones de extintores'},
            {'module': 'extinguisher', 'action': 'edit', 'description': 'Editar inspecciones de extintores'},
            {'module': 'extinguisher', 'action': 'delete', 'description': 'Eliminar inspecciones de extintores'},
            
            # Botiquines
            {'module': 'first_aid', 'action': 'view', 'description': 'Ver inspecciones de botiquines'},
            {'module': 'first_aid', 'action': 'create', 'description': 'Registrar inspecciones de botiquines'},
            {'module': 'first_aid', 'action': 'edit', 'description': 'Editar inspecciones de botiquines'},
            {'module': 'first_aid', 'action': 'delete', 'description': 'Eliminar inspecciones de botiquines'},
            
            # Procesos
            {'module': 'process', 'action': 'view', 'description': 'Ver inspecciones de procesos'},
            {'module': 'process', 'action': 'create', 'description': 'Registrar inspecciones de procesos'},
            {'module': 'process', 'action': 'edit', 'description': 'Editar inspecciones de procesos'},
            {'module': 'process', 'action': 'delete', 'description': 'Eliminar inspecciones de procesos'},
            
            # Almacenamiento
            {'module': 'storage', 'action': 'view', 'description': 'Ver inspecciones de almacenamiento'},
            {'module': 'storage', 'action': 'create', 'description': 'Registrar inspecciones de almacenamiento'},
            {'module': 'storage', 'action': 'edit', 'description': 'Editar inspecciones de almacenamiento'},
            {'module': 'storage', 'action': 'delete', 'description': 'Eliminar inspecciones de almacenamiento'},
            
            # Montacargas
            {'module': 'forklift', 'action': 'view', 'description': 'Ver inspecciones de montacargas'},
            {'module': 'forklift', 'action': 'create', 'description': 'Registrar inspecciones de montacargas'},
            {'module': 'forklift', 'action': 'edit', 'description': 'Editar inspecciones de montacargas'},
            {'module': 'forklift', 'action': 'delete', 'description': 'Eliminar inspecciones de montacargas'},
        ]
        
        self.stdout.write(self.style.SUCCESS('\n=== Inicializando Permisos ===\n'))
        
        created_count = 0
        existing_count = 0
        
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
                existing_count += 1
                self.stdout.write(f'  [--] {perm.description}')
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'Permisos creados: {created_count}'))
        self.stdout.write(f'Permisos existentes: {existing_count}')
        self.stdout.write(self.style.SUCCESS(f'Total de permisos: {Permission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nAhora ejecuta: python manage.py init_roles'))
