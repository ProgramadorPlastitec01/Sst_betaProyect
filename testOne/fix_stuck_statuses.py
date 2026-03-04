"""
Script de reparación: Actualiza inspecciones padre que quedaron en
'Seguimiento en proceso' pero cuyos seguimientos ya están todos cerrados.

Ejecutar con: python fix_stuck_statuses.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inspections.models import (
    ExtinguisherInspection,
    FirstAidInspection,
    ProcessInspection,
    StorageInspection,
    ForkliftInspection,
)

TERMINAL_STATUSES = ['Cerrada', 'Cerrada con seguimientos']
STUCK_STATUS = 'Seguimiento en proceso'
TARGET_STATUS = 'Cerrada con seguimientos'


def fix_module(model, label):
    """Corrige inspecciones padre con estado atascado en un módulo dado."""
    stuck = model.objects.filter(status=STUCK_STATUS)
    fixed = 0
    still_open = 0

    for insp in stuck:
        follow_ups = insp.follow_ups.all()
        if not follow_ups.exists():
            print(f"  [{label}] ID {insp.pk}: Sin seguimientos – se omite.")
            continue

        # ¿Todos los seguimientos están en estados terminales?
        pending = follow_ups.exclude(status__in=TERMINAL_STATUSES)
        if not pending.exists():
            insp.status = TARGET_STATUS
            insp.save()
            fixed += 1
            fup_info = ", ".join([f"#{f.pk}({f.status})" for f in follow_ups])
            print(f"  [{label}] ID {insp.pk}: ACTUALIZADO -> '{TARGET_STATUS}' | Seguimientos: {fup_info}")
        else:
            still_open += 1
            pending_info = ", ".join([f"#{f.pk}({f.status})" for f in pending])
            print(f"  [{label}] ID {insp.pk}: PENDIENTE - Seguimientos aun abiertos: {pending_info}")

    return fixed, still_open


print("=" * 60)
print("REPARACIÓN DE ESTADOS ATASCADOS")
print("=" * 60)

total_fixed = 0
total_open = 0

modules = [
    (ExtinguisherInspection, "Extintores"),
    (FirstAidInspection,     "Botiquines"),
    (ProcessInspection,      "Procesos"),
    (StorageInspection,      "Almacenamiento"),
    (ForkliftInspection,     "Montacargas"),
]

for model, label in modules:
    count = model.objects.filter(status=STUCK_STATUS).count()
    print(f"\n[{label}] — {count} inspección(es) con estado '{STUCK_STATUS}'")
    if count > 0:
        f, o = fix_module(model, label)
        total_fixed += f
        total_open += o

print("\n" + "=" * 60)
print(f"RESUMEN: {total_fixed} actualizada(s), {total_open} con seguimientos aún pendientes.")
print("=" * 60)
