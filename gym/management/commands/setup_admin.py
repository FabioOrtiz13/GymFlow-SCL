from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gym.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Inicializa usuario administrador'

    def handle(self, *args, **kwargs):
        # Crear/obtener admin
        if User.objects.filter(username='admin').exists():
            admin = User.objects.get(username='admin')
            self.stdout.write(self.style.WARNING('⚠️  Admin ya existe'))
        else:
            admin = User.objects.create_superuser('admin', 'admin@gym.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Admin creado'))
        
        # Asegurar que es superuser y staff
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        
        # Crear o actualizar perfil
        perfil, created = PerfilUsuario.objects.get_or_create(
            user=admin,
            defaults={'tipo_usuario': 'administrador'}
        )
        
        if not created:
            perfil.tipo_usuario = 'administrador'
            perfil.save()
            self.stdout.write(self.style.SUCCESS('✓ Perfil actualizado'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Perfil creado'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✓ Administrador configurado'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\nCredenciales:')
        self.stdout.write('  Usuario: admin')
        self.stdout.write('  Contraseña: admin123')
        self.stdout.write('  URL: http://localhost:8000/admin/')
        self.stdout.write('\n')

