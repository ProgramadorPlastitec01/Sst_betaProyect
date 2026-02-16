---
description: Lógica de Inspecciones y Visualización de Seguimientos
---

# Lógica de Inspecciones y Visualización

Este flujo describe cómo se filtran y visualizan las inspecciones y sus seguimientos en el sistema.

## Filtrado de Inspecciones
En todos los listados (`ExtinguisherListView`, `FirstAidListView`, `InspectionListView`), se aplica el siguiente filtro:

```python
qs = qs.filter(parent_inspection__isnull=True)
```

Esto asegura que **solo las inspecciones iniciales (padres)** sean visibles en las tablas principales. Las inspecciones de seguimiento (hijas) se ocultan para mantener la integridad visual y lógica.

## Indicador de Seguimiento
Para las inspecciones iniciales que tienen seguimientos asociados, se muestra un indicador visual en la columna de estado:

- **Texto:** "Seguimientos: X" (donde X es el número de seguimientos)

## Visualización de Estado
Los estados de las inspecciones se codifican por colores para facilitar la identificación visual:
- **Programada**: Gris (badge-secondary)
- **En proceso**: Azul (badge-primary)
- **Cerrada / Realizada**: Verde (badge-success)
- **Cerrada con Hallazgos**: Naranja (badge-warning)
- **Vencida / No Cumple**: Rojo (badge-danger)

El estado inicial predeterminado para nuevas inspecciones es **"Programada"**.

Esto se logra mediante una anotación en la consulta:
```python
qs = qs.annotate(follow_ups_count=Count('follow_ups'))
```

En el dashboard (`InspectionListView`), esta información se agrega manualmente al diccionario de datos de cada inspección mediante `getattr(insp, 'follow_ups_count', 0)`.

## Métricas
El cálculo de métricas en `MatrixContextMixin` también excluye los seguimientos para proporcionar conteos precisos de inspecciones programadas vs realizadas.
