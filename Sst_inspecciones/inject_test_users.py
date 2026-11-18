import os
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser
from roles.models import Role

def inject_users(count=10):
    first_names = ["Juan", "Maria", "Carlos", "Ana", "Luis", "Elena", "Pedro", "Sofia", "Jorge", "Lucia", "Andres", "Marta", "Ricardo", "Isabel", "Fernando", "Clara"]
    last_names = ["Garcia", "Rodriguez", "Lopez", "Martinez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Vargas", "Morales", "Castro"]
    
    roles = list(Role.objects.all())
    if not roles:
        print("No se encontraron roles en la base de datos.")
        return

    created_count = 0
    for i in range(count):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        username = f"{fname.lower()}.{lname.lower()}.{random.randint(10, 99)}"
        email = f"{username}@plastitec.com"
        
        # Ensure unique email/username
        if CustomUser.objects.filter(email=email).exists():
            continue
            
        role = random.choice(roles)
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password="TestPassword123!",
            first_name=fname,
            last_name=lname,
            role=role,
            document_number=str(random.randint(10000000, 99999999))
        )
        print(f"Usuario creado: {fname} {lname} ({email}) - Rol: {role.name}")
        created_count += 1
    
    print(f"\nTotal de usuarios inyectados: {created_count}")

if __name__ == "__main__":
    inject_users(10)
