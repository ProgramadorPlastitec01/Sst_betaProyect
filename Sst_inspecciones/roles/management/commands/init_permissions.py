from django.core.management.base import BaseCommand
from roles.models import Permission, PERMISSION_MATRIX


class Command(BaseCommand):
    help = (
        'Sincroniza los permisos en BD con la PERMISSION_MATRIX definida en roles/models.py.\n'
        'Crea los permisos faltantes, reactiva los que deben existir y desactiva los obsoletos.\n'
        'No elimina registros — preserva integridad referencial con roles existentes.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin ejecutar cambios en BD.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        action_labels = dict(Permission.ACTION_CHOICES)
        module_labels = dict(Permission.MODULE_CHOICES)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No se realizarán cambios en la BD.\n'))

        self.stdout.write(self.style.SUCCESS('\n=== Sincronizando Permisos con PERMISSION_MATRIX ===\n'))

        # Construir el conjunto de codenames válidos según la matriz
        valid_codenames = set()
        permissions_to_sync = []

        for module_code, actions in PERMISSION_MATRIX.items():
            module_label = module_labels.get(module_code, module_code.capitalize())
            for action_code in actions:
                action_label = action_labels.get(action_code, action_code.capitalize())
                codename = f'{module_code}_{action_code}'
                valid_codenames.add(codename)
                permissions_to_sync.append({
                    'module': module_code,
                    'action': action_code,
                    'codename': codename,
                    'description': f'{action_label} en {module_label}',
                })

        created_count = 0
        reactivated_count = 0
        already_ok_count = 0

        # Crear o reactivar permisos de la matriz
        for perm_data in permissions_to_sync:
            try:
                perm = Permission.objects.get(codename=perm_data['codename'])
                # Existe: verificar si necesita actualización
                changed = False
                if not perm.is_active:
                    if not dry_run:
                        perm.is_active = True
                        perm.save()
                    reactivated_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  [REACTIVADO] {perm_data["codename"]}: {perm_data["description"]}'
                    ))
                    changed = True
                # Actualizar descripción si cambió
                if perm.description != perm_data['description'] or perm.module != perm_data['module'] or perm.action != perm_data['action']:
                    if not dry_run:
                        perm.description = perm_data['description']
                        perm.module = perm_data['module']
                        perm.action = perm_data['action']
                        perm.save()
                    if not changed:
                        self.stdout.write(self.style.SUCCESS(
                            f'  [ACTUALIZADO] {perm_data["codename"]}: {perm_data["description"]}'
                        ))
                        changed = True
                if not changed:
                    already_ok_count += 1
                    self.stdout.write(f'  [OK] {perm_data["codename"]}')

            except Permission.DoesNotExist:
                if not dry_run:
                    Permission.objects.create(
                        module=perm_data['module'],
                        action=perm_data['action'],
                        codename=perm_data['codename'],
                        description=perm_data['description'],
                        is_active=True,
                    )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  [CREADO] {perm_data["codename"]}: {perm_data["description"]}'
                ))

        # Desactivar permisos obsoletos (no en la matriz actual)
        obsolete_qs = Permission.objects.exclude(codename__in=valid_codenames).filter(is_active=True)
        obsolete_count = obsolete_qs.count()
        if obsolete_count > 0:
            self.stdout.write(self.style.WARNING(f'\n  Permisos obsoletos encontrados ({obsolete_count}):'))
            for p in obsolete_qs:
                self.stdout.write(self.style.WARNING(f'    >> {p.codename}: {p.description}'))
                if not dry_run:
                    p.is_active = False
                    p.save()
        else:
            self.stdout.write(self.style.SUCCESS('\n  Sin permisos obsoletos.'))

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'  Permisos creados:      {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Permisos reactivados:  {reactivated_count}'))
        self.stdout.write(f'  Permisos sin cambios:  {already_ok_count}')
        self.stdout.write(self.style.WARNING(f'  Permisos desactivados: {obsolete_count}'))

        if not dry_run:
            total_active = Permission.objects.filter(is_active=True).count()
            self.stdout.write(self.style.SUCCESS(f'\n  Total activos en BD:   {total_active}'))
            self.stdout.write(self.style.SUCCESS('\n¡Sincronización completada!'))
            self.stdout.write(self.style.SUCCESS('Ejecuta: python manage.py init_roles  (si necesitas recrear roles base)'))
        else:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No se aplicaron cambios.'))
