import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from roles.models import Permission, Role

def setup_reset_password_permission():
    # Create the permission if it doesn't exist
    perm, created = Permission.objects.get_or_create(
        module='users',
        action='reset_password',
        defaults={
            'codename': 'users_reset_password',
            'description': 'Restablecer contraseña de usuarios'
        }
    )
    
    if created:
        print(f"Permiso '{perm}' creado exitosamente.")
    else:
        print(f"Permiso '{perm}' ya existe.")

    # Assign it to the Administrador role
    try:
        admin_role = Role.objects.get(name='Administrador')
        if not admin_role.permissions.filter(id=perm.id).exists():
            admin_role.permissions.add(perm)
            print(f"Permiso '{perm}' asignado al rol Administrador.")
        else:
            print(f"El rol Administrador ya tiene el permiso '{perm}'.")
    except Role.DoesNotExist:
        print("El rol 'Administrador' no existe.")

if __name__ == "__main__":
    setup_reset_password_permission()
