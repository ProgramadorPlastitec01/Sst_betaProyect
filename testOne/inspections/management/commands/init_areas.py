from django.core.management.base import BaseCommand
from inspections.models import Area

class Command(BaseCommand):
    help = 'Inicializa las areas estandarizadas de la organizacion'

    def handle(self, *args, **options):
        areas = [
            'DIRECCION GENERAL',
            'PRODUCION INDUSTRIAL',
            'ADMINISTRATIVOS',
            'AUTOMATIZACION',
            'COSTOS',
            'DIRECCION COMERCIAL COLOMBIA',
            'LOGISTICA Y COMERCIO EXTERIOR',
            'TECNOLOGÍA DE INFORMACIÓN',
            'SEGURIDAD Y SALUD EN EL TRABAJO',
            'DIRECCION MANUFACTURA',
            'DIRECCION MAQUINARIA Y AUTOMATIZACION',
            'SEGURIDAD',
            'ALMACEN',
            'EXTRUSIÓN',
            'INYECCIÓN',
            'CONTABILIDAD',
            'ALMACEN PRODUCTO TERMINADO',
            'GERENCIA GENERAL',
            'DIRECCION DE PRODUCCION',
            'DIRECCION DE MANTENIMIENTO Y SERVICIOS GENERALES',
            'GESTION DE CALIDAD',
            'DIRECCION COMERCIAL LOGISTICA Y COMERCIO EXTERIOR',
            'DIRECCION DE RECURSOS HUMANOS',
            'PRODUCCION INSUMOS',
            'PRODUCCION FARMACEUTICA',
            'MANTENIMIENTO FARMACEUTICO',
            'MANTENIMIENTO INSUMOS',
            'PROYECTOS',
            'DISEÑO DE MAQUINARIA',
            'ALMACEN PRODUCTO EN PROCESO',
            'COMPRAS',
        ]

        created_count = 0
        existing_count = 0

        for area_name in areas:
            area, created = Area.objects.get_or_create(
                name=area_name,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [OK] Area creada: {area_name}'))
            else:
                existing_count += 1
                self.stdout.write(f'  [--] Area existente: {area_name}')

        self.stdout.write(self.style.SUCCESS(f'\n=== Resumen ==='))
        self.stdout.write(self.style.SUCCESS(f'Areas creadas: {created_count}'))
        self.stdout.write(f'Areas existentes: {existing_count}')
        self.stdout.write(self.style.SUCCESS(f'Total: {created_count + existing_count}'))
