---
description: Corrección de Filtros de Área y Visualización de Año en Cronograma
---

# Corrección de Filtros y Display de Año

## Problemas Resueltos

### 1. Desplegable de Áreas con Números
- **Antes:** El filtro mostraba los IDs de las áreas (ej: 1, 2, 3), lo cual era confuso.
- **Ahora:** Se modificó la consulta en `get_context_data` para usar `values_list('area__name', flat=True)`. El filtro ahora muestra los nombres de las áreas (ej: Almacén, Producción), y la lógica de filtrado busca por nombre (`area__name__icontains`).

### 2. Año Incorrecto (2025) y Default
- **Antes:** El título mostraba "2025" fijo si no había selección, y cargaba todos los datos mezclados.
- **Ahora:** 
    - Se eliminó el valor fijo "2025".
    - Al cargar la página sin filtros, se selecciona automáticamente el **año actual** (2026).
    - El título refleja el año seleccionado o "Histórico Completo" si se elige ver todos.

## Archivos Modificados
- `inspections/views.py`: Método `MatrixContextMixin.get_context_data`.

## Verificación
- El desplegable de "Área" debe mostrar nombres de texto.
- Al entrar al módulo, el título debe decir "Cronograma de Actividades - 2026" (o el año actual).
- La tabla debe mostrar datos correspondientes al año del título.
