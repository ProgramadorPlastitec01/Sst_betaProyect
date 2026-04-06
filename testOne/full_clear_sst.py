import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import transaction
from gestion_activos.models import Asset, MovimientoActivo, ExtintorDetail, MontacargasDetail, BotiquinDetail
from inspections.models import (
    InspectionSchedule, 
    ExtinguisherInspection, FirstAidInspection, 
    ProcessInspection, StorageInspection, ForkliftInspection,
    InspectionEvidence, InspectionSignature, FirstAidSignature,
    ProcessSignature, StorageSignature, ForkliftSignature
)

def full_clear():
    print("=== Iniciando eliminación completa de Activos e Inspecciones ===")
    
    with transaction.atomic():
        # 1. Eliminar Inspecciones (y sus ítems vinculados por CASCADE si aplica, 
        # o explícitamente si queremos conteos precisos)
        
        print("\n--- Eliminando Módulos de Inspección ---")
        
        # Evidencias (Genéricas)
        ev_count, _ = InspectionEvidence.objects.all().delete()
        print(f"  [InspectionEvidence] {ev_count} registros.")
        
        # Firmas (a veces están el tablas separadas o heredadas)
        sig_count = 0
        sig_count += InspectionSignature.objects.all().delete()[0]
        sig_count += FirstAidSignature.objects.all().delete()[0]
        sig_count += ProcessSignature.objects.all().delete()[0]
        sig_count += StorageSignature.objects.all().delete()[0]
        sig_count += ForkliftSignature.objects.all().delete()[0]
        print(f"  [Signatures] {sig_count} registros.")
        
        # Módulos principales
        ins_models = [
            ExtinguisherInspection, FirstAidInspection, 
            ProcessInspection, StorageInspection, ForkliftInspection
        ]
        
        for model in ins_models:
            count, _ = model.objects.all().delete()
            print(f"  [{model.__name__}] {count} registros.")
            
        # Cronograma (Programaciones)
        sched_count, _ = InspectionSchedule.objects.all().delete()
        print(f"  [InspectionSchedule] {sched_count} registros.")
        
        # 2. Eliminar Activos
        print("\n--- Eliminando Activos e Inventario ---")
        
        # Movimientos
        mov_count, _ = MovimientoActivo.objects.all().delete()
        print(f"  [MovimientoActivo] {mov_count} registros.")
        
        # Detalles específicos (se eliminarían por CASCADE al borrar Asset, 
        # pero los borramos antes para ver el conteo)
        ExtintorDetail.objects.all().delete()
        MontacargasDetail.objects.all().delete()
        BotiquinDetail.objects.all().delete()
        
        # Activos Base
        asset_count, _ = Asset.objects.all().delete()
        print(f"  [Asset] {asset_count} registros (incluyendo detalles vinculados).")

    print("\n=== ¡ELIMINACIÓN COMPLETADA EXITOSAMENTE! ===")
    print("Nota: Areas, Tipos de Activo, Planos y Usuarios se mantuvieron intactos.")

if __name__ == "__main__":
    full_clear()
