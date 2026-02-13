# ⚠️ ESTADO ACTUAL - ESTANDARIZACIÓN DE ÁREAS

## ✅ COMPLETADO

1. ✅ Modelo `Area` creado en `inspections/models.py`
2. ✅ Migración `0009_area.py` aplicada - Tabla creada
3. ✅ 31 áreas oficiales pobladas en la BD
4. ✅ Admin registrado para gestión futura
5. ✅ Comando `init_areas` funcional

## ⚠️ PROBLEMA DETECTADO

**Error al migrar:**
```
IntegrityError: The row in table 'inspections_storageinspection' with primary key '2' 
has an invalid foreign key: inspections_storageinspection.area_id contains a value 'ti' 
that does not have a corresponding value in inspections_area.id.
```

**Causa:**
- Ya existen registros en la BD con valores de área como texto libre
- Django intentó convertir directamente CharField → ForeignKey
- Los valores de texto no coinciden con IDs de la tabla Area

## 🔧 SOLUCIÓN REQUERIDA

### Opción 1: Migración de Datos en Dos Pasos (RECOMENDADA)

#### Paso 1: Agregar campo temporal `area_fk`
```python
# Nueva migración
area_fk = models.ForeignKey(
    'Area',
    on_delete=models.PROTECT,
    null=True,  # Temporal
    blank=True,
    verbose_name="Área (Nuevo)"
)
```

#### Paso 2: Migración de datos
```python
def migrate_area_data(apps, schema_editor):
    Area = apps.get_model('inspections', 'Area')
    InspectionSchedule = apps.get_model('inspections', 'InspectionSchedule')
    
    for schedule in InspectionSchedule.objects.all():
        area_text = schedule.area  # Texto actual
        
        # Intentar encontrar área exacta
        area_obj = Area.objects.filter(name__iexact=area_text).first()
        
        # Si no existe, crear nueva área
        if not area_obj:
            area_obj, _ = Area.objects.get_or_create(
                name=area_text.upper(),
                defaults={'is_active': True}
            )
        
        schedule.area_fk = area_obj
        schedule.save()
```

#### Paso 3: Eliminar campo viejo y renombrar
```python
# Eliminar campo 'area' (CharField)
# Renombrar 'area_fk' → 'area'
```

### Opción 2: Limpiar BD y empezar de cero (MÁS SIMPLE)

Si no hay datos importantes:
```bash
# Eliminar BD
rm db.sqlite3

# Recrear todo
python manage.py migrate
python manage.py init_areas
python manage.py createsuperuser
```

## 📋 PRÓXIMOS PASOS

### Si hay datos importantes (Opción 1):
1. Revertir cambios en models.py (volver CharField)
2. Crear migración con campo `area_fk` (ForeignKey nullable)
3. Crear migración de datos personalizada
4. Eliminar campo `area` viejo
5. Renombrar `area_fk` → `area`

### Si NO hay datos importantes (Opción 2):
1. Eliminar `db.sqlite3`
2. Eliminar carpeta `inspections/migrations` (excepto `__init__.py`)
3. Recrear migraciones desde cero
4. Aplicar migraciones
5. Poblar áreas
6. Crear superusuario

## 🎯 RECOMENDACIÓN

**¿Hay datos importantes en la BD actual?**
- **SÍ** → Usar Opción 1 (migración en pasos)
- **NO** → Usar Opción 2 (recrear BD) - MÁS RÁPIDO

---

**ESPERANDO DECISIÓN DEL USUARIO**
