"""
Script para eliminar TODAS las inspecciones y reiniciar sus IDs (secuencias PostgreSQL).
NO elimina: usuarios, areas, activos, cronograma, roles, configuraciones.

Uso:
  cd C:\\Users\\Programador.ti2\\Desktop\\Antigravity\\testOne
  python clear_inspections.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

TABLES = [
    'inspections_inspectionevidence',
    'inspections_extinguishersignature',
    'inspections_firstaidsignature',
    'inspections_processsignature',
    'inspections_storagesignature',
    'inspections_forkliftsignature',
    'inspections_extinguisheritem',
    'inspections_firstaiditem',
    'inspections_processcheckitem',
    'inspections_storagecheckitem',
    'inspections_forkliftcheckitem',
    'inspections_extinguisherinspection',
    'inspections_firstaidinspection',
    'inspections_processinspection',
    'inspections_storageinspection',
    'inspections_forkliftinspection',
    'inspections_inspectionschedule',
]

def table_exists(cursor, table_name):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
    """, [table_name])
    return cursor.fetchone()[0]

print("=" * 55)
print("  LIMPIEZA DE INSPECCIONES - PostgreSQL")
print("=" * 55)

with connection.cursor() as cursor:
    for table in TABLES:
        if table_exists(cursor, table):
            cursor.execute('TRUNCATE TABLE "{}" RESTART IDENTITY CASCADE'.format(table))
            print("  [OK] {}".format(table))
        else:
            print("  [--] {} --- no encontrada (omitida)".format(table))

print("=" * 55)
print("  LISTO. Todos los IDs reiniciados desde 1.")
print("  Usuarios, areas, activos y roles intactos.")
print("=" * 55)
