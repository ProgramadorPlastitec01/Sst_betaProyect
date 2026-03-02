"""
Carga masiva de 200 extintores (EXT-1 al EXT-200) y datos iniciales de TipoExtintor.
"""
import os
import django
import random
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inspections.models import Area
from gestion_activos.models import AssetType, Asset, ExtintorDetail, TipoExtintor

# ── 1. Tipos de Extintor iniciales ──────────────────────────────────────────
tipos_iniciales = [
    'Polvo quimico seco (PQS)',
    'H2O Agua a presion',
    'Solkaflam',
    'CO2 Gas Carbonico',
    'Multiproposito',
]

print("=== Creando tipos de extintor ===")
for nombre in tipos_iniciales:
    obj, created = TipoExtintor.objects.get_or_create(
        nombre=nombre,
        defaults={'activo': True}
    )
    status = 'CREADO' if created else 'YA EXISTE'
    print(f"  [{status}] {obj.nombre}")

# ── 2. Obtener referencias necesarias ───────────────────────────────────────
try:
    asset_type_extintor = AssetType.objects.get(name='Extintor')
except AssetType.DoesNotExist:
    print("\nERROR: No existe el AssetType 'Extintor'. Verifique la configuracion.")
    exit(1)

tipo_pqs = TipoExtintor.objects.get(nombre='Polvo quimico seco (PQS)')
areas = list(Area.objects.filter(is_active=True))

if not areas:
    print("\nERROR: No hay areas activas en el sistema.")
    exit(1)

capacidades = [5, 10, 15, 20, 50]
fecha_adquisicion = date(2024, 1, 1)
fecha_recarga = date(2024, 11, 25)
fecha_vencimiento = date(2025, 11, 25)
observaciones = "Informacion de extintor PENDIENTE POR VALIDAR"

# ── 3. Carga masiva EXT-1 al EXT-200 ────────────────────────────────────────
print("\n=== Cargando 200 extintores ===")
creados = 0
ya_existentes = 0

for i in range(1, 201):
    codigo = f"EXT-{i}"

    if Asset.objects.filter(code=codigo).exists():
        ya_existentes += 1
        continue

    area = random.choice(areas)
    capacidad = random.choice(capacidades)

    asset = Asset.objects.create(
        code=codigo,
        asset_type=asset_type_extintor,
        area=area,
        fecha_adquisicion=fecha_adquisicion,
        activo=True,
        observaciones=observaciones,
    )

    ExtintorDetail.objects.create(
        asset=asset,
        tipo_agente=tipo_pqs,
        capacidad_kg=capacidad,
        fecha_recarga=fecha_recarga,
        fecha_vencimiento=fecha_vencimiento,
    )
    creados += 1

print(f"  Extintores creados:      {creados}")
print(f"  Codigos ya existentes:   {ya_existentes}")
print(f"\nTotal extintores en BD: {Asset.objects.filter(asset_type=asset_type_extintor).count()}")
print("\nCarga masiva completada.")
