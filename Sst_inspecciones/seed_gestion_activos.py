"""
Script de datos iniciales para el modulo de Gestion de Activos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from gestion_activos.models import AssetType
from roles.models import Permission, Role

# 1. Tipos de Activo
tipos_iniciales = [
    {'name': 'Extintor', 'description': 'Extintores de incendio de todo tipo de agente.'},
    {'name': 'Montacargas', 'description': 'Equipos de montacargas de combustible o electrico.'},
]

for tipo_data in tipos_iniciales:
    obj, created = AssetType.objects.get_or_create(
        name=tipo_data['name'],
        defaults={'description': tipo_data['description']}
    )
    status = 'CREADO' if created else 'YA EXISTE'
    print(f"  [{status}] Tipo de activo: {obj.name}")

# 2. Permisos del modulo 'assets'
permisos_activos = [
    ('assets', 'view',   'assets_view',   'Ver Gestion de Activos'),
    ('assets', 'create', 'assets_create', 'Crear Activos'),
    ('assets', 'edit',   'assets_edit',   'Editar Activos'),
    ('assets', 'delete', 'assets_delete', 'Eliminar Activos'),
]

created_perms = []
for module, action, codename, description in permisos_activos:
    perm, created = Permission.objects.get_or_create(
        module=module,
        action=action,
        defaults={'codename': codename, 'description': description}
    )
    created_perms.append(perm)
    status = 'CREADO' if created else 'YA EXISTE'
    print(f"  [{status}] Permiso: {codename}")

# 3. Asignar todos los permisos al rol Administrador
try:
    admin_role = Role.objects.get(name='Administrador')
    for perm in created_perms:
        admin_role.permissions.add(perm)
    print(f"\n  [OK] Permisos de activos asignados al rol 'Administrador'")
except Role.DoesNotExist:
    print("\n  [ADVERTENCIA] Rol 'Administrador' no encontrado. Asigna los permisos manualmente en /roles/.")

print("\nDatos iniciales del modulo Gestion de Activos completados.")
