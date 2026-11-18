
from gestion_activos.models import Asset
import django
import os

def analyze():
    assets = Asset.objects.all()
    print('--- Analisis de Datos para Cumplimiento ---')
    base = [a for a in assets if not a.temporal and a.estado_actual != 'FUERA_DE_SERVICIO']
    optimos = [a for a in base if a.estado_actual in ('ACTIVO', 'OPERATIVO')]
    no_optimos = [a for a in base if a.estado_actual not in ('ACTIVO', 'OPERATIVO')]
    
    print(f'Total Base (Fijos no Fuera de Servicio): {len(base)}')
    print(f'Total Optimos (ACTIVO/OPERATIVO): {len(optimos)}')
    print(f'Diferencia (No Optimos): {len(no_optimos)}')
    
    if no_optimos:
        print('\nDetalle de activos que bajan el cumplimiento:')
        for a in no_optimos:
            print(f'- Codigo: {a.code} | Estado: {a.estado_actual} | Tipo: {a.tipo_nombre}')
    else:
        print('\nNo se encontraron activos que bajen el cumplimiento.')

if __name__ == "__main__":
    analyze()
