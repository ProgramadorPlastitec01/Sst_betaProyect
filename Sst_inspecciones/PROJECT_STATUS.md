# 📊 Estado Actual del Proyecto SST

**Fecha:** 2026-10-23
**Entorno actual:** desplegado en una VM de pruebas internas (no producción)

---

## 🎯 RESUMEN EJECUTIVO

Sistema de Gestión de Seguridad y Salud en el Trabajo (SST) para Plastitec, con 8 apps Django funcionales: cronograma e inspecciones, gestión de activos físicos, ubicación en planos SVG, y un sistema RBAC propio **completamente implementado y aplicado** (no solo modelado) en más de 100 vistas.

Este documento reemplaza versiones anteriores (fechadas 2026-02-12) que describían el sistema sin los módulos de Gestión de Activos y Planos, y marcaban el control de acceso como pendiente cuando en realidad ya está en producción de pruebas.

---

## ✅ MÓDULOS IMPLEMENTADOS

### 1. **Autenticación y Usuarios**
**Estado:** ✅ Operativo
**Funcionalidades:**
- Login/Logout por email (no por username)
- CRUD de usuarios
- Firma digital (base64) por usuario
- Asignación de roles

**Archivos:**
- `users/models.py` - CustomUser (AbstractUser + email como USERNAME_FIELD)
- `users/views.py` - Vistas CRUD
- `users/management/commands/create_datamaster.py` - Creación de usuario admin inicial

---

### 2. **Sistema de Inspecciones**
**Estado:** ✅ Operativo
**Tipos de Inspección:**
1. ✅ Cronograma Anual (con generación automática de la siguiente ocurrencia según frecuencia)
2. ✅ Extintores
3. ✅ Botiquines (Primeros Auxilios)
4. ✅ Procesos
5. ✅ Almacenamiento
6. ✅ Montacargas

**Funcionalidades:**
- CRUD completo para cada tipo, construido sobre un modelo base abstracto compartido (`BaseInspection`)
- Filtros por año, área, estado
- Asignación de responsables
- Firmas digitales por inspección
- Evidencia fotográfica (relación genérica, reutilizable en cualquier módulo)
- Reportes consolidados con exportación a Excel
- Notificaciones Toastr en todas las operaciones

**Archivos:**
- `inspections/models.py` - Area, InspectionSchedule, BaseInspection + 5 modelos concretos
- `inspections/views.py` - ~2600 líneas (candidato a dividirse por módulo, como ya se hizo con `area_views.py`)
- `inspections/management/commands/init_areas.py` - Semilla del catálogo de áreas

---

### 3. **Gestión de Activos** ⭐ (no documentado en versiones previas de este archivo)
**Estado:** ✅ Operativo
**Funcionalidades:**
- Inventario de activos físicos (extintores, montacargas, botiquines), independiente del checklist de inspección
- Ficha de detalle específica por tipo de activo
- Estado calculado dinámicamente (vencido, próximo a vencer, en mantenimiento, sin inspección, etc.)
- Trazabilidad completa de movimientos (salida, reemplazo con temporal, retorno, baja) — bitácora de auditoría, nunca se eliminan registros

**Archivos:**
- `gestion_activos/models.py` - Asset, AssetType, TipoExtintor, ExtintorDetail, MontacargasDetail, BotiquinDetail, MovimientoActivo
- `gestion_activos/views.py` - ~850 líneas, 20 vistas protegidas por RBAC

**Ruta:** `/activos/`

---

### 4. **Planos** ⭐ (no documentado en versiones previas de este archivo)
**Estado:** ✅ Operativo
**Funcionalidades:**
- Ubicación visual de activos sobre planos SVG
- Historial de posiciones por activo

**Archivos:**
- `planos/models.py` - UbicacionActivo
- `planos/views.py` - ~210 líneas

**Ruta:** `/planos/`

---

### 5. **Sistema RBAC (Roles y Permisos)**
**Estado:** ✅ **Completo y aplicado** — no es solo infraestructura de modelos, está funcionando en producción de pruebas
**Funcionalidades:**
- ✅ CRUD de roles
- ✅ `PERMISSION_MATRIX` como fuente única de verdad (11 módulos, 48 permisos activos)
- ✅ `RolePermissionRequiredMixin` aplicado en más de 100 vistas, en las 8 apps del proyecto
- ✅ `RoleSimulationMiddleware`: un Administrador puede simular la vista con permisos de otro rol sin modificar la base de datos
- ✅ Template tags de permisos (`roles/templatetags/permission_tags.py`) para UI condicional (sidebar, botones)
- ✅ Protección del rol Administrador (siempre con todos los permisos activos)
- ✅ 6 roles base creados por `init_roles`: Administrador, Equipo SST, Almacenista, Brigadista, Montacarguista, Consulta — todos editables después desde la interfaz

**Archivos:**
- `roles/models.py` - Permission, Role, PERMISSION_MATRIX
- `roles/mixins.py` - RolePermissionRequiredMixin
- `roles/middleware.py` - RoleSimulationMiddleware
- `roles/context_processors.py` - expone estado de simulación a templates
- `roles/management/commands/` - init_permissions, init_roles

---

### 6. **Sistema de Notificaciones**
**Estado:** ✅ Operativo
**Tecnología:** Toastr.js
**Módulos con notificaciones:** Login, Usuarios, Cronograma, Extintores, Botiquines, Procesos, Almacenamiento, Montacargas

**Archivos:**
- `static/js/notifications.js` - Configuración global
- `templates/base.html` - Integración

---

### 7. **Configuración del Sistema**
**Estado:** ✅ Operativo
- Parámetros clave-valor tipados (`string`, `number`, `boolean`), editables desde la interfaz
- Catálogo de Planos (`Plano`), consumido por `gestion_activos` y `planos`

**Ruta:** `/configuration/` y `/configuration/advanced/`

---

## 📊 ESTADÍSTICAS DEL SISTEMA (verificadas sobre el código, no estimadas)

### Base de datos
```
Motor activo: PostgreSQL (sst_db) — SQLite ya no está en uso, db.sqlite3 es un archivo obsoleto
Apps con modelos: 8 (users, roles, inspections, notifications, system_config, gestion_activos, planos)

Migraciones por app (proxy de cuánto ha evolucionado cada una):
├── inspections:      34
├── roles:              8
├── gestion_activos:    7
├── users:              3
├── system_config:      2
├── notifications:      1
└── planos:             1
```

### Permisos y Roles
```
Módulos protegibles: 11 (users, roles, schedule, extinguisher, first_aid, process,
                          storage, forklift, assets, reports, planos)
Total de permisos activos: 48
Roles base creados por init_roles: 6
Vistas protegidas con RolePermissionRequiredMixin: 100+ en 8 apps
```

### Código
```
inspections/views.py:       ~2600 líneas (el archivo más grande del proyecto)
gestion_activos/views.py:   ~850 líneas
planos/views.py:            ~210 líneas
```

---

## 🗂️ ESTRUCTURA DEL PROYECTO (real)

```
testOne/                       # NO es la raíz del repo git (.git está en el directorio padre)
├── core/                      # Configuración Django
├── users/                     # Autenticación y usuarios
├── inspections/                # Cronograma + 5 módulos de inspección + áreas + reportes
├── roles/                      # RBAC: roles, permisos, simulación de rol
├── gestion_activos/             # ⭐ Inventario de activos físicos
├── planos/                      # ⭐ Ubicación de activos en planos SVG
├── system_config/               # Configuración clave-valor + catálogo de Planos
├── notifications/                # Notificaciones internas
├── templates/                    # Templates globales
├── static/                       # CSS, JS, imágenes
├── CLAUDE.md                     # Guía de arquitectura para Claude Code
├── TECHNICAL_DOCS.md             # Documentación técnica detallada
└── manage.py
```

---

## ⚙️ TECNOLOGÍAS UTILIZADAS

### Backend
- Python 3.13
- Django 5.2.7
- **PostgreSQL** (activo en la VM de pruebas)

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5
- Font Awesome 6.4
- Toastr.js
- Google Fonts (Inter)

---

## ⚠️ PUNTOS PENDIENTES ANTES DE SALIR DEL ENTORNO DE PRUEBAS

No bloquean el uso actual en la VM de pruebas internas, pero son requisito antes de exponer el sistema a usuarios externos o a internet:

1. `SECRET_KEY` sigue siendo la generada por defecto por Django — rotar y mover a variable de entorno
2. `DEBUG = True` junto con `ALLOWED_HOSTS = ['*']` — con `DEBUG` activo, un error 500 expone el stacktrace completo (incluye `SECRET_KEY` y la contraseña de PostgreSQL) a quien lo provoque
3. Credenciales de PostgreSQL hardcodeadas en texto plano en `core/settings.py`
4. No hay backups automáticos configurados (los existentes son manuales/ad-hoc)

## 🧹 DEUDA TÉCNICA CONOCIDA

- `inspections/views.py` (~2600 líneas) es candidato a dividirse por módulo, siguiendo el precedente de `area_views.py`
- La raíz del proyecto acumula scripts de mantenimiento ad-hoc (`tmp_*.py`, `clear_data.py`, `full_clear_sst.py`, `setup_permissions.py`, etc.) que no forman parte del flujo soportado — usar los comandos `manage.py` documentados en README/TECHNICAL_DOCS en su lugar
- `db.sqlite3` sigue en el repo aunque no está en uso

---

## 📈 PRÓXIMOS PASOS

### Mejoras futuras
1. [ ] Exportar inspecciones a PDF
2. [ ] Notificaciones por email
3. [ ] Historial de cambios (audit log) más allá del ya existente para movimientos de activos
4. [ ] API REST
5. [ ] Endurecimiento de configuración para despliegue fuera del entorno de pruebas (ver sección de puntos pendientes arriba)

---

## 📞 SOPORTE

**Cliente:** Plastitec
**Proyecto:** Sistema de Gestión SST
**Última actualización:** 2026-10-23 — documento regenerado contrastando cada afirmación contra el código fuente real (no contra versiones previas de este archivo)
