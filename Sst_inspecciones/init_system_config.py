import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from system_config.models import SystemConfig

configs = [
    {
        'key': 'dias_seguimiento_auto',
        'value': '15',
        'config_type': 'number',
        'category': 'inspecciones',
        'description': 'Días para programar automáticamente un seguimiento.'
    },
    {
        'key': 'dias_aviso_programacion',
        'value': '3',
        'config_type': 'number',
        'category': 'notificaciones',
        'description': 'Días previos para avisar sobre programaciones pendientes.'
    },
    {
        'key': 'notificaciones_activas',
        'value': 'true',
        'config_type': 'boolean',
        'category': 'general',
        'description': 'Activa o desactiva notificaciones internas del sistema.'
    }
]

for conf in configs:
    obj, created = SystemConfig.objects.get_or_create(
        key=conf['key'],
        defaults=conf
    )
    if not created:
        print(f"Config '{conf['key']}' already exists.")
    else:
        print(f"Config '{conf['key']}' created.")
