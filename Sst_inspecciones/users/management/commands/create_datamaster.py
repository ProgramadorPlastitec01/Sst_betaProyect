from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea el superusuario datamaster'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = 'datamaster'
        email = 'admin@example.com'
        password = 'admin123'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'El usuario "{username}" ya existe.'))
            return
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(self.style.SUCCESS('[OK] Superusuario creado exitosamente!'))
        self.stdout.write(f'   Usuario: {username}')
        self.stdout.write(f'   Email: {email}')
        self.stdout.write(f'   Contrasena: {password}')
        self.stdout.write(self.style.SUCCESS('\nPuedes iniciar sesion ahora!'))
