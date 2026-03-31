import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from gestion_activos.models import Asset, AssetType
from django.utils import timezone
from datetime import timedelta

at = AssetType.objects.filter(name__icontains='otiqu').first() # Use "otiqu" to avoid encoding issues
if at:
    assets = Asset.objects.filter(asset_type=at)
    print(f"Total botiquines: {assets.count()}")
    for a in assets:
        last = a.botiquin_detail.fecha_ultima_revision if hasattr(a, 'botiquin_detail') else 'N/A'
        next_rev = a.botiquin_detail.fecha_proxima_revision if hasattr(a, 'botiquin_detail') else 'N/A'
        print(f"Code: {a.code}, Last: {last}, Next: {next_rev}, Status: {a.estado_actual}, Label: {a.estado_label}")
else:
    print("No se encontró el tipo de activo Botiquín")
