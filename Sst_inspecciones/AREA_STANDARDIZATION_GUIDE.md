# 🔧 ESTANDARIZACIÓN DEL CAMPO ÁREA - GUÍA DE IMPLEMENTACIÓN

## ✅ COMPLETADO

### 1. Modelo Area Creado
- ✅ `inspections/models.py` - Modelo `Area` agregado
- ✅ Campos: `name`, `is_active`, `created_at`, `updated_at`
- ✅ Ordenamiento por nombre
- ✅ Unique constraint en `name`

### 2. Comando de Gestión Creado
- ✅ `inspections/management/commands/init_areas.py`
- ✅ Poblará las 31 áreas oficiales

### 3. Admin Registrado
- ✅ `inspections/admin.py` - AreaAdmin configurado
- ✅ Permite gestión futura de áreas

---

## ⏳ PENDIENTE (EJECUTAR EN ORDEN)

### PASO 1: Crear Migración Inicial
```bash
python manage.py makemigrations inspections
```
**Descripción:** Creará la tabla `inspections_area`

### PASO 2: Aplicar Migración
```bash
python manage.py migrate
```
**Descripción:** Ejecuta la migración en la base de datos

### PASO 3: Poblar Áreas Iniciales
```bash
python manage.py init_areas
```
**Descripción:** Crea las 31 áreas oficiales en la BD

### PASO 4: Actualizar Modelos de Inspección
**Archivos a modificar:**
- `InspectionSchedule.area` - Cambiar de CharField a ForeignKey
- `BaseInspection.area` - Cambiar de CharField a ForeignKey

**Código a cambiar:**
```python
# ANTES
area = models.CharField(max_length=200, verbose_name="Área/Ubicación")

# DESPUÉS
area = models.ForeignKey(
    'Area',
    on_delete=models.PROTECT,
    verbose_name="Área/Ubicación"
)
```

### PASO 5: Crear Migración de Conversión
```bash
python manage.py makemigrations inspections
```
**Nota:** Django detectará el cambio de CharField a ForeignKey

### PASO 6: Migración de Datos (Script Custom)
Crear migración de datos para convertir textos existentes a ForeignKeys:
```python
# migrations/XXXX_convert_area_to_fk.py
def convert_areas(apps, schema_editor):
    Area = apps.get_model('inspections', 'Area')
    InspectionSchedule = apps.get_model('inspections', 'InspectionSchedule')
    
    # Mapear áreas existentes
    for schedule in InspectionSchedule.objects.all():
        area_text = schedule.area
        area_obj, _ = Area.objects.get_or_create(name=area_text)
        schedule.area = area_obj
        schedule.save()
```

### PASO 7: Actualizar Formularios
**Archivos a modificar:**
- `inspections/forms.py` - Todos los formularios que usan `area`

**Cambio en widgets:**
```python
# ANTES
widgets = {
    'area': forms.TextInput(attrs={'class': 'form-control'}),
}

# DESPUÉS
widgets = {
    'area': forms.Select(attrs={'class': 'form-control'}),
}

# O mejor aún, usar queryset filtrado:
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['area'].queryset = Area.objects.filter(is_active=True)
```

### PASO 8: Aplicar Migración Final
```bash
python manage.py migrate
```

### PASO 9: Testing
1. Verificar que los dropdowns muestran las áreas
2. Crear nueva inspección y seleccionar área
3. Verificar que se guarda correctamente
4. Verificar que áreas existentes se muestran correctamente

---

## 📋 ÁREAS OFICIALES (31 total)

1. DIRECCION GENERAL
2. PRODUCION INDUSTRIAL
3. ADMINISTRATIVOS
4. AUTOMATIZACION
5. COSTOS
6. DIRECCION COMERCIAL COLOMBIA
7. LOGISTICA Y COMERCIO EXTERIOR
8. TECNOLOGÍA DE INFORMACIÓN
9. SEGURIDAD Y SALUD EN EL TRABAJO
10. DIRECCION MANUFACTURA
11. DIRECCION MAQUINARIA Y AUTOMATIZACION
12. SEGURIDAD
13. ALMACEN
14. EXTRUSIÓN
15. INYECCIÓN
16. CONTABILIDAD
17. ALMACEN PRODUCTO TERMINADO
18. GERENCIA GENERAL
19. DIRECCION DE PRODUCCION
20. DIRECCION DE MANTENIMIENTO Y SERVICIOS GENERALES
21. GESTION DE CALIDAD
22. DIRECCION COMERCIAL LOGISTICA Y COMERCIO EXTERIOR
23. DIRECCION DE RECURSOS HUMANOS
24. PRODUCCION INSUMOS
25. PRODUCCION FARMACEUTICA
26. MANTENIMIENTO FARMACEUTICO
27. MANTENIMIENTO INSUMOS
28. PROYECTOS
29. DISEÑO DE MAQUINARIA
30. ALMACEN PRODUCTO EN PROCESO
31. COMPRAS

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### Migración de Datos Existentes
Si ya hay inspecciones en la BD con áreas como texto libre:
1. Primero crear el modelo Area
2. Poblar con áreas oficiales
3. Crear script de migración de datos
4. Mapear textos existentes a Areas (crear nuevas si no existen)
5. Luego cambiar el campo a ForeignKey

### Opción Alternativa (Más Segura)
1. Crear campo nuevo `area_fk` como ForeignKey
2. Migrar datos del campo viejo al nuevo
3. Eliminar campo viejo
4. Renombrar `area_fk` a `area`

---

## 🎯 PRÓXIMO PASO INMEDIATO

**EJECUTAR:**
```bash
python manage.py makemigrations inspections
python manage.py migrate
python manage.py init_areas
```

Luego continuar con la actualización de los modelos de inspección.
