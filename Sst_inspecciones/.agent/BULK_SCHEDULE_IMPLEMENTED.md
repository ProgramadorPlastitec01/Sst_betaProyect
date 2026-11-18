---
description: Implementación y Corrección de Generación Masiva de Cronogramas
---

# Estado Actual del Módulo de Cronogramas

## Lógica de Generación Masiva (Actualizada)
Se ha implementado una lógica robusta en `InspectionCreateView` para generar automáticamente las programaciones anuales basándose en la periodicidad seleccionada.

### Frecuencias Soportadas
El sistema mapea las siguientes frecuencias a intervalos de meses:
- **MensualDTO**: 1 mes
- **Bimestral**: 2 meses (Agregada recientemente)
- **Trimestral**: 3 meses
- **Cuatrimestral**: 4 meses
- **Semestral**: 6 meses
- **Anual**: 12 meses

### Reglas de Negocio Implementadas
1. **Validación de Año**: Solo se generan fechas dentro del año seleccionado en el formulario (o año de la fecha base si falla la conversión).
2. **Duplicados**: Se verifica si ya existe una programación para la misma área, tipo y fecha antes de crear una nueva.
3. **Persistencia**: Se crean objetos `InspectionSchedule` reales en la base de datos con estado "Programada".
4. **Feedback**: El usuario recibe un mensaje indicando el número exacto de programaciones adicionales generadas.

## Correcciones Recientes
- Se reemplazó la estructura `if/elif` por un diccionario de mapeo (`freq_map`) para garantizar la coincidencia exacta de los términos de frecuencia.
- Se agregó manejo de errores (`try/except`) para la extracción del año del formulario.
- Se mejoró el mensaje de éxito para proporcionar feedback cuantitativo.

# Archivos Relevantes
- `inspections/views.py`: Contiene la lógica principal en `InspectionCreateView.form_valid`.
- `inspections/models.py`: Define las opciones de frecuencia y métodos auxiliares.
- `inspections/forms.py`: Maneja la selección del año.
