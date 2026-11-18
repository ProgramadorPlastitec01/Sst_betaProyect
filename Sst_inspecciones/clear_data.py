"""
Script para limpiar datos de inspecciones y activos.
Elimina SOLO registros operativos. No toca configuraciones, usuarios, areas ni cronograma.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# ── Inspecciones ──────────────────────────────────────────────────────────────
from inspections.models import (
    ExtinguisherInspection,
    FirstAidInspection,
    ProcessInspection,
    StorageInspection,
    ForkliftInspection,
)

modelos_inspecciones = [
    ExtinguisherInspection,
    FirstAidInspection,
    ProcessInspection,
    StorageInspection,
    ForkliftInspection,
]

print("=== Eliminando inspecciones ===")
for modelo in modelos_inspecciones:
    count, _ = modelo.objects.all().delete()
    print(f"  [{modelo.__name__}] {count} registro(s) eliminado(s)")

# ── Gestión de Activos ────────────────────────────────────────────────────────
from gestion_activos.models import Asset, ExtintorDetail, MontacargasDetail

print("\n=== Eliminando activos ===")
# Los detalles se eliminan en cascada al borrar Asset, pero los borramos
# explícitamente para reportar el conteo
ext_count, _ = ExtintorDetail.objects.all().delete()
mnt_count, _ = MontacargasDetail.objects.all().delete()
asset_count, _ = Asset.objects.all().delete()

print(f"  [ExtintorDetail]     {ext_count} registro(s) eliminado(s)")
print(f"  [MontacargasDetail]  {mnt_count} registro(s) eliminado(s)")
print(f"  [Asset]              {asset_count} registro(s) eliminado(s)")

print("\nLimpieza completada. Tablas de AssetType, Areas, Usuarios y Cronograma intactas.")
