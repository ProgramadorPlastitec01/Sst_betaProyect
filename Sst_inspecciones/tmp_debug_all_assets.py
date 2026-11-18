import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from gestion_activos.models import Asset
from django.db.models import Prefetch

all_assets = Asset.objects.all().prefetch_related('extintor_detail', 'montacargas_detail', 'botiquin_detail')
print(f"Total: {all_assets.count()}")
for a in all_assets:
    print(f"Code: {a.code}, Type: {a.asset_type.name}, Status: {a.estado_actual}, Label: {a.estado_label}")
