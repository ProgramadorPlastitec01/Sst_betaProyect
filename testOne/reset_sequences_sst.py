import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

TABLES = [
    # Gestión de Activos
    'gestion_activos_asset',
    'gestion_activos_movimientoactivo',
    'gestion_activos_extintordetail',
    'gestion_activos_montacargasdetail',
    'gestion_activos_botiquindetail',
    
    # Inspecciones
    'inspections_inspectionevidence',
    'inspections_inspectionsignature',
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

def restart_sequences():
    print("=== Restableciendo consecutivos (Secuencias PostgreSQL) ===")
    
    with connection.cursor() as cursor:
        for table in TABLES:
            try:
                # TRUNCATE con RESTART IDENTITY es la forma más limpia en PG
                # de vaciar y reiniciar el ID a 1
                cursor.execute(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE;')
                print(f"  [OK] Consecutivo reiniciado para: {table}")
            except Exception as e:
                # Si la tabla no existe o hay error, lo reportamos pero seguimos
                print(f"  [!] No se pudo reiniciar {table}: {e}")
                
    print("\n=== ¡TODOS LOS CONSECUTIVOS HAN SIDO REINICIADOS A 1! ===")

if __name__ == "__main__":
    restart_sequences()
