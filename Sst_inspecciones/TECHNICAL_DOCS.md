# 📋 Documentación Técnica — Sistema de Gestión de Inspecciones SG-SST

> **Framework:** Django 5.2.7  
> **Base de datos:** PostgreSQL (activa — ver §7). SQLite queda solo como bloque comentado de referencia en `settings.py`; `db.sqlite3` en la raíz es un archivo obsoleto sin uso.  
> **Lenguaje:** Python 3.13  
> **Entorno actual:** desplegado en una VM de pruebas internas (no producción pública)  
> **Última revisión de este documento:** 2026-10-23, contrastada directamente contra el código fuente

---

## Tabla de Contenidos

1. [Descripción General del Sistema](#1-descripción-general-del-sistema)
2. [Arquitectura MVT](#2-arquitectura-mvt)
3. [Estructura de Carpetas](#3-estructura-de-carpetas)
4. [Apps Django y sus Responsabilidades](#4-apps-django-y-sus-responsabilidades)
5. [Modelos de Datos y Relaciones](#5-modelos-de-datos-y-relaciones)
6. [Flujo de Autenticación y Autorización (RBAC)](#6-flujo-de-autenticación-y-autorización-rbac)
7. [Configuración del Proyecto](#7-configuración-del-proyecto)
8. [Dependencias y Librerías](#8-dependencias-y-librerías)
9. [Flujo de una Solicitud HTTP](#9-flujo-de-una-solicitud-http)
10. [Instalación y Despliegue](#10-instalación-y-despliegue)

---

## 1. Descripción General del Sistema

El **Sistema de Gestión de Inspecciones SG-SST** es una aplicación web desarrollada en Django orientada a la gestión integral del Sistema de Gestión de Seguridad y Salud en el Trabajo. Permite planificar, ejecutar, registrar y reportar inspecciones periódicas de distintos tipos de activos y áreas dentro de una organización.

### Funcionalidades principales

| Módulo | Descripción |
|---|---|
| **Cronograma** | Planificación anual de inspecciones por tipo, área, frecuencia y responsable |
| **Extintores** | Inspección checklist de extintores (R-RH-SST-019) |
| **Botiquines** | Inspección checklist de botiquines de primeros auxilios (R-RH-SST-020) |
| **Procesos** | Inspección de instalaciones y procesos (R-RH-SST-030) |
| **Almacenamiento** | Inspección de áreas de almacenamiento (R-RH-SST-031) |
| **Montacargas** | Inspección de montacargas y equipos de elevación (R-RH-SST-022) |
| **Reportes** | Vista unificada de inspecciones históricas con estadísticas, filtros y exportación a Excel |
| **Gestión de Activos** | Inventario de activos físicos (extintores, montacargas, botiquines) con estado calculado y trazabilidad de movimientos |
| **Planos** | Ubicación de activos sobre planos SVG, con historial de posiciones |
| **Usuarios** | Gestión de usuarios con autenticación por email |
| **Roles y Permisos** | Control de acceso granular por módulo y acción (RBAC) |
| **Notificaciones** | Alertas internas con clasificación por tipo |
| **Configuración** | Parámetros del sistema editables desde la interfaz, catálogo de Planos |

### Usuarios del sistema

El sistema emplea autenticación basada en **email** (no en username, aunque `username` se mantiene por herencia de `AbstractUser`). Los roles **no están hardcodeados**: se gestionan 100% desde la base de datos vía la interfaz de Roles. El comando `init_roles` crea una semilla inicial de 6 roles:

- **Administrador** — Acceso total a todos los módulos (trato especial por nombre, no por flag)
- **Equipo SST** — Ver, crear, editar y consultar inspecciones/cronogramas
- **Almacenista** — Inspecciones de almacenamiento e inventario
- **Brigadista** — Inspecciones de extintores y botiquines
- **Montacarguista** — Ver, crear y consultar inspecciones de montacargas
- **Consulta** — Solo lectura

---

## 2. Arquitectura MVT

Django implementa el patrón **Model–View–Template (MVT)**, una variante del MVC donde el framework actúa como el "Controller".

```
Navegador (HTTP Request)
        │
        ▼
┌─────────────────────┐
│   Django Router     │  ← core/urls.py + app/urls.py
│  (URL Dispatcher)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│      View / CBV     │  ← inspections/views.py, users/views.py, etc.
│  (Lógica de negocio)│    Usa: LoginRequiredMixin, RolePermissionRequiredMixin
└────────┬────────────┘
         │        │
         │        ▼
         │  ┌──────────────┐
         │  │    Model     │  ← inspections/models.py, roles/models.py, etc.
         │  │  (ORM/DB)    │  ← db.sqlite3
         │  └──────────────┘
         │
         ▼
┌─────────────────────┐
│     Template        │  ← templates/inspections/*.html
│  (Capa de Presentac.)│   Usa: Django Template Language (DTL)
└────────┬────────────┘
         │
         ▼
Navegador (HTTP Response)
```

### Componentes clave del proyecto

| Componente | Implementación |
|---|---|
| **Models** | Clases Python que mapean tablas SQLite vía ORM de Django |
| **Views** | Class-Based Views (CBV) usando `ListView`, `CreateView`, `UpdateView`, `DetailView`, `DeleteView`, `View` |
| **Templates** | Archivos `.html` en `templates/` con DTL, herencia de base y bloques |
| **Forms** | `ModelForm` y `Form` en `forms.py` de cada app |
| **Mixins** | `RolePermissionRequiredMixin` en `roles/mixins.py` para autorización |
| **URLs** | Enrutamiento jerárquico: `core/urls.py` incluye las URLs de cada app |

---

## 3. Estructura de Carpetas

```
testOne/                          ← Raíz del proyecto (NO es la raíz del repo git — .git está en el directorio padre)
│
├── core/                         ← Paquete de configuración del proyecto
│   ├── settings.py               ← Configuración principal de Django
│   ├── urls.py                   ← Enrutador raíz
│   ├── views.py                  ← Vista de configuración general
│   ├── wsgi.py                   ← Punto de entrada WSGI
│   └── asgi.py                   ← Punto de entrada ASGI
│
├── users/                        ← App de gestión de usuarios
│   ├── models.py                 ← CustomUser (AbstractUser + email auth)
│   ├── views.py                  ← Login, logout, CRUD de usuarios
│   ├── forms.py                  ← UserCreationForm personalizado
│   ├── urls.py                   ← Rutas de /accounts/
│   ├── management/commands/      ← create_datamaster (usuario admin inicial)
│   └── templates/users/          ← Templates de usuarios
│
├── roles/                        ← App de Roles y Permisos (RBAC)
│   ├── models.py                 ← Role, Permission, PERMISSION_MATRIX (fuente única de verdad)
│   ├── mixins.py                 ← RolePermissionRequiredMixin
│   ├── middleware.py             ← RoleSimulationMiddleware (simulación de rol sin tocar BD)
│   ├── context_processors.py     ← Expone estado de simulación a los templates
│   ├── templatetags/             ← permission_tags.py
│   ├── views.py                  ← CRUD de roles y asignación de permisos
│   ├── urls.py                   ← Rutas de /roles/
│   ├── management/commands/      ← init_permissions, init_roles
│   └── templates/roles/          ← Templates de roles
│
├── inspections/                  ← App principal de inspecciones (la más grande)
│   ├── models.py                 ← Area, InspectionSchedule, BaseInspection (abstracto) + 5 módulos
│   ├── views.py                  ← Vistas de cronograma y de los 5 módulos (~2600 líneas)
│   ├── area_views.py             ← CRUD de Áreas (ya separado de views.py)
│   ├── forms.py                  ← Formularios de inspección
│   ├── urls.py                   ← Rutas de /inspections/
│   ├── templatetags/             ← inspection_tags.py
│   ├── management/commands/      ← init_areas
│   └── templates/inspections/    ← Templates de inspecciones
│
├── gestion_activos/               ← ⭐ App de inventario de activos físicos (no documentada antes)
│   ├── models.py                 ← Asset, AssetType, TipoExtintor, ExtintorDetail,
│   │                                MontacargasDetail, BotiquinDetail, MovimientoActivo
│   ├── views.py                  ← CRUD de activos y gestión de movimientos (~850 líneas)
│   ├── urls.py                   ← Rutas de /activos/
│   └── templates/gestion_activos/
│
├── planos/                        ← ⭐ App de ubicación de activos en planos SVG (no documentada antes)
│   ├── models.py                 ← UbicacionActivo (historial de posiciones)
│   ├── views.py                  ← ~210 líneas
│   ├── urls.py                   ← Rutas de /planos/
│   └── templates/planos/
│
├── notifications/                ← App de notificaciones internas
│   ├── models.py                 ← NotificationGroup, Notification
│   ├── views.py                  ← Vistas de notificaciones
│   └── urls.py                   ← Rutas de /notifications/
│
├── system_config/                ← App de configuración del sistema
│   ├── models.py                 ← SystemConfig (clave-valor tipado), Plano
│   ├── views.py                  ← CRUD de configuraciones
│   └── urls.py                   ← Rutas de /configuration/advanced/
│
├── templates/                    ← Templates globales (base, auth, etc.)
│   ├── base.html                 ← Layout principal con sidebar y navbar
│   ├── dashboard.html            ← Dashboard con KPIs y gráfico de cumplimiento
│   └── registration/             ← Templates de autenticación
│
├── static/                       ← Archivos estáticos globales
│   ├── css/                      ← Hojas de estilo personalizadas
│   ├── js/                       ← JavaScript global
│   └── images/                   ← Imágenes del sistema
│
├── manage.py                     ← CLI de Django
├── requirements.txt              ← Dependencias del proyecto
├── CLAUDE.md                     ← Guía de arquitectura para Claude Code
└── TECHNICAL_DOCS.md             ← Este documento
```

> `db.sqlite3` sigue presente en la raíz pero **no está en uso**: la base de datos activa es PostgreSQL (ver §7).

---

## 4. Apps Django y sus Responsabilidades

### 4.1 `core` — Configuración del Proyecto

No es una app Django en sentido estricto, sino el **paquete de configuración** generado por `django-admin startproject`. Contiene:

- `settings.py`: toda la configuración del sistema
- `urls.py`: enrutador raíz que delega a cada app
- `views.py`: única vista propia — `ConfigurationView` (panel de configuración general)

---

### 4.2 `users` — Gestión de Usuarios

Extiende el sistema de autenticación de Django con un modelo `CustomUser`.

**Responsabilidades:**
- Autenticación por **email** (no por username)
- CRUD de usuarios con asignación de rol
- Almacenamiento de **firma digital** (Base64)
- Restablecimiento de contraseña por parte de Administradores

**Ruta base:** `/accounts/`

---

### 4.3 `roles` — Control de Acceso Basado en Roles (RBAC)

Implementa un sistema de permisos granular propio, independiente del sistema nativo de Django (`django.contrib.auth.Permission` no se usa para esto).

**Responsabilidades:**
- `PERMISSION_MATRIX` en `roles/models.py` es la **fuente única de verdad**: define qué `(módulo, acción)` existen (11 módulos, 48 permisos activos en total)
- Agrupar permisos en **Roles**, gestionables 100% desde la BD/interfaz — no hay roles hardcodeados salvo el trato especial para `"Administrador"` (acceso total implícito en `has_perm_custom`)
- Exponer `RolePermissionRequiredMixin` (`roles/mixins.py`) — mixin de CBV, **no** decorador — para proteger vistas; se usa en >100 vistas a lo largo de 8 apps
- `RoleSimulationMiddleware` (`roles/middleware.py`): permite a un Administrador simular la vista con los permisos de otro rol, parcheando `has_perm_custom` en memoria por request (nada se escribe en BD)
- `permission_tags.py` y `context_processors.role_simulation`: exponen los permisos y el estado de simulación a los templates (sidebar condicional, etc.)
- CRUD de roles desde la interfaz web
- Comandos: `init_permissions` (sincroniza BD con `PERMISSION_MATRIX`) e `init_roles` (crea la semilla de 6 roles base)

**Ruta base:** `/roles/`

---

### 4.4 `inspections` — Módulo Principal de Inspecciones

La app más grande del sistema. Gestiona el ciclo completo de vida de las inspecciones.

**Responsabilidades:**
- **Cronograma anual** (`InspectionSchedule`): planificación por módulo, área, frecuencia y responsable; `generate_next_schedule()` crea automáticamente la siguiente ocurrencia según la frecuencia al cerrar una inspección
- **5 módulos de inspección**, todos heredando de `BaseInspection` (modelo abstracto con `inspection_date`, `area`, `inspector`, `schedule_item`, `general_status`, `observations`), con checklist, firmas digitales y reportes:
  - Extintores, Botiquines, Procesos, Almacenamiento, Montacargas
- **Gestión de Áreas** (`Area`): catálogo centralizado compartido, también usado por `gestion_activos`
- **`InspectionEvidence`**: evidencia fotográfica vía relación genérica (`ContentType`), adjuntable a cualquier inspección o ítem
- **Módulo de Reportes**: vista consolidada con estadísticas, filtros avanzados, gráfico de tendencia mensual y exportación a Excel
- Soporte para **inspecciones de seguimiento** (follow-up) anidadas

`views.py` concentra ~2600 líneas con el patrón List/Create/Update/Detail/Sign/Report repetido por cada uno de los 5 módulos; `area_views.py` ya fue separado como precedente para dividir el resto si crece más.

**Ruta base:** `/inspections/`

---

### 4.4bis `gestion_activos` — Inventario de Activos Físicos ⭐

App independiente del checklist de inspecciones: lleva el **registro de activos físicos** y su ciclo de vida.

**Responsabilidades:**
- `Asset`: ficha base de un activo (código, tipo, área, plano opcional), vinculada 1-a-1 a una tabla de detalle según su tipo (`ExtintorDetail`, `MontacargasDetail`, `BotiquinDetail`)
- `Asset.estado_actual`: estado calculado dinámicamente (vencido, próximo a vencer, en mantenimiento, sin inspección, etc.) combinando fechas y, para extintores, el estado persistido de movimiento
- `MovimientoActivo`: bitácora de auditoría (salida, reemplazo con temporal, retorno, baja) — **nunca se eliminan registros**, es la fuente de verdad del estado de movimiento
- El campo `temporal` en `Asset` distingue activos de reemplazo (creados por el flujo de movimientos) de los creados manualmente

**Ruta base:** `/activos/`

---

### 4.4ter `planos` — Ubicación de Activos en Planos ⭐

App que posiciona activos de `gestion_activos` sobre planos SVG (`system_config.Plano`), manteniendo un historial de posiciones (`UbicacionActivo`).

**Ruta base:** `/planos/`

---

### 4.5 `notifications` — Notificaciones Internas

Sistema de alertas internas para usuarios del sistema.

**Responsabilidades:**
- Crear y gestionar notificaciones individuales por usuario
- Clasificar por tipo: `sistema`, `alerta`, `inspección`
- Gestionar grupos de notificación con suscriptores
- Marcar como leídas desde la interfaz

**Ruta base:** `/notifications/`

---

### 4.6 `system_config` — Configuración del Sistema

Almacén de parámetros de configuración en formato clave-valor, más el catálogo de Planos.

**Responsabilidades:**
- Persistir configuraciones editables (nombre de empresa, logo, etc.)
- Tipado de valores: `string`, `number`, `boolean`
- Agrupación por categoría
- Acceso programático vía `SystemConfig.get_value(key, default)`
- `Plano`: catálogo de planos nombrados, consumido por `gestion_activos` (FK opcional en `Asset`) y por `planos`

**Ruta base:** `/configuration/advanced/`

---

## 5. Modelos de Datos y Relaciones

### 5.1 Diagrama de Relaciones Simplificado

```
CustomUser ──────────────── Role
    │           FK              │
    │                          │ M2M
    │                       Permission
    │
    ├── Notification (FK)
    ├── NotificationGroup (M2M)
    │
    ├── InspectionSchedule (FK: responsible)
    │
    ├── ExtinguisherInspection (FK: inspector)
    │       └── ExtinguisherItem (FK)
    │       └── InspectionSignature (FK)
    │
    ├── FirstAidInspection (FK: inspector)
    │       └── FirstAidItem (FK)
    │       └── FirstAidSignature (FK)
    │
    ├── ProcessInspection (FK: inspector)
    │       └── ProcessCheckItem (FK)
    │       └── ProcessSignature (FK)
    │
    ├── StorageInspection (FK: inspector)
    │       └── StorageCheckItem (FK)
    │       └── StorageSignature (FK)
    │
    └── ForkliftInspection (FK: inspector)
            └── ForkliftCheckItem (FK)
            └── (sin tabla de firmas propia)

Area ──── InspectionSchedule (FK)
     ──── ExtinguisherInspection (FK)
     ──── FirstAidInspection (FK)
     ... (todos los módulos)
     ──── Asset (FK, gestion_activos)

Asset (gestion_activos) ──── AssetType (FK)
     │                  ──── Plano (FK opcional, system_config)
     ├── ExtintorDetail (1-a-1) ──── TipoExtintor (FK)
     ├── MontacargasDetail (1-a-1)
     ├── BotiquinDetail (1-a-1)
     └── MovimientoActivo (FK: activo, activo_relacionado)

UbicacionActivo (planos) ──── Asset (FK) + Plano (FK)

SystemConfig  (tabla independiente, sin relaciones FK)
```

---

### 5.2 Descripción de Modelos

#### `CustomUser` (app: `users`)

| Campo | Tipo | Descripción |
|---|---|---|
| `email` | `EmailField` (unique) | Identificador principal de autenticación |
| `username` | `CharField` | Alias (heredado de AbstractUser) |
| `first_name`, `last_name` | `CharField` | Nombre completo |
| `document_number` | `CharField` | Número de documento de identidad |
| `role` | `FK → Role` | Rol asignado (determina permisos) |
| `digital_signature` | `TextField` | Firma digitalizada en Base64 |
| `is_active` | `BooleanField` | Habilita/deshabilita el usuario |

---

#### `Role` (app: `roles`)

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | `CharField` (unique) | Nombre del rol (ej. "Administrador") |
| `description` | `TextField` | Descripción del rol |
| `permissions` | `M2M → Permission` | Permisos habilitados para este rol |
| `is_active` | `BooleanField` | Si el rol está habilitado |
| `is_system_role` | `BooleanField` | Protege roles del sistema contra eliminación |

#### `Permission` (app: `roles`)

| Campo | Tipo | Opciones |
|---|---|---|
| `module` | `CharField` | `users`, `inspections`, `schedule`, `extinguisher`, `first_aid`, `process`, `storage`, `forklift`, `roles`, `reports` |
| `action` | `CharField` | `view`, `create`, `edit`, `delete`, `reset_password` |
| `codename` | `CharField` (unique) | Auto-generado: `{module}_{action}` |

---

#### `InspectionSchedule` (app: `inspections`)

| Campo | Tipo | Descripción |
|---|---|---|
| `year` | `IntegerField` | Año del cronograma |
| `area` | `FK → Area` | Área a inspeccionar |
| `inspection_type` | `CharField` | Tipo de inspección (extinguisher, first_aid, etc.) |
| `frequency` | `CharField` | Mensual, Bimestral, Trimestral, etc. |
| `scheduled_date` | `DateField` | Fecha programada |
| `responsible` | `FK → CustomUser` | Responsable asignado |
| `status` | `CharField` | Programada / En Proceso / Cerrada / Vencida |
| `observations` | `TextField` | Notas adicionales |

---

#### Modelos de Inspección (patrón repetido por módulo)

Cada módulo de inspección sigue el mismo patrón:

```
{Módulo}Inspection          ← Cabecera de inspección
    ├── inspector            FK → CustomUser
    ├── area                 FK → Area
    ├── inspection_date      DateField
    ├── schedule             FK → InspectionSchedule (opcional)
    ├── status               CharField (Abierta / Cerrada / Cerrada con Hallazgos)
    ├── overall_status       CharField (Cumple / No Cumple / Parcial)
    ├── parent_inspection    FK → self (para seguimientos anidados)
    └── observations         TextField

{Módulo}CheckItem / {Módulo}Item  ← Ítem de checklist
    ├── inspection           FK → {Módulo}Inspection
    ├── item_name            CharField
    ├── status               CharField (Bueno / Regular / Malo o Existe / No Existe)
    ├── response             CharField (Si / No / NA)
    ├── observations         CharField
    └── registered_by        FK → CustomUser

{Módulo}Signature           ← Firma digital por usuario
    ├── inspection           FK → {Módulo}Inspection
    ├── user                 FK → CustomUser
    ├── signature            TextField (Base64 PNG)
    └── signed_at            DateTimeField
```

---

#### `Area` (app: `inspections`)

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | `CharField` (unique) | Nombre del área (ej. "Planta 1") |
| `is_active` | `BooleanField` | Si el área está activa |

---

#### `Notification` (app: `notifications`)

| Campo | Tipo | Descripción |
|---|---|---|
| `user` | `FK → CustomUser` | Destinatario |
| `title` | `CharField` | Título de la notificación |
| `message` | `TextField` | Cuerpo del mensaje |
| `link` | `CharField` | URL de acción relacionada |
| `notification_type` | `CharField` | `sistema`, `alerta`, `inspección` |
| `is_read` | `BooleanField` | Si el usuario la ha leído |

---

#### `SystemConfig` (app: `system_config`)

| Campo | Tipo | Descripción |
|---|---|---|
| `key` | `CharField` (unique) | Clave de configuración |
| `value` | `CharField` | Valor almacenado como string |
| `config_type` | `CharField` | `string`, `number`, `boolean` |
| `category` | `CharField` | Agrupación lógica |
| `is_editable` | `BooleanField` | Si puede editarse desde la UI |

---

## 6. Flujo de Autenticación y Autorización (RBAC)

### 6.1 Autenticación

```
Usuario ingresa email + contraseña
        │
        ▼
LoginView (users/views.py)
        │
        ├── Django verifica credenciales contra CustomUser
        │   USERNAME_FIELD = 'email'
        │
        ├── Si válidas → crea sesión (SESSION_COOKIE_AGE = 1800s)
        │
        └── Redirect a LOGIN_REDIRECT_URL = 'dashboard'
```

**Configuración de sesión:**
- Duración: **30 minutos** de inactividad (`SESSION_COOKIE_AGE = 1800`)
- Renovación automática en cada request (`SESSION_SAVE_EVERY_REQUEST = True`)
- Cierre al cerrar el navegador (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`)

---

### 6.2 Autorización (RBAC)

El sistema implementa un **Control de Acceso Basado en Roles (RBAC)** personalizado, independiente del sistema de permisos nativo de Django.

```
Request llega a una CBV protegida
        │
        ▼
RolePermissionRequiredMixin.dispatch()
        │
        ├── ¿Usuario autenticado?
        │     NO → redirect a /accounts/login/
        │
        ├── ¿Tiene permission_required?
        │     NO → permite acceso (vista pública)
        │
        └── user.has_perm_custom(module, action)
                │
                ├── ¿is_superuser? → True (acceso total)
                │
                ├── ¿role.name == 'Administrador'? → True
                │
                ├── ¿role is None o role.is_active == False? → False
                │
                └── role.has_permission(module, action)
                        │
                        └── Permission.objects.filter(
                                module=module,
                                action=action,
                                is_active=True
                            ).exists()
```

**Ejemplo de protección de una vista:**

```python
class ExtinguisherCreateView(RolePermissionRequiredMixin, CreateView):
    permission_required = ('extinguisher', 'create')
    model = ExtinguisherInspection
    form_class = ExtinguisherInspectionForm
```

**Módulos protegibles** (`roles/models.py` → `PERMISSION_MATRIX`, 48 permisos activos en total):

| Código | Nombre visible | Acciones |
|---|---|---|
| `users` | Usuarios | view, create, edit, delete, reset_password |
| `roles` | Roles | view, create, edit, delete, details |
| `schedule` | Cronograma | view, create, edit, delete |
| `extinguisher` | Extintores | view, create, edit, delete, details |
| `first_aid` | Botiquines | view, create, edit, delete, details |
| `process` | Procesos | view, create, edit, delete, details |
| `storage` | Almacenamiento | view, create, edit, delete, details |
| `forklift` | Montacargas | view, create, edit, delete, details |
| `assets` | Gestión de Activos | view, details, create, edit, delete, gestionar_movimientos |
| `reports` | Reportes | view |
| `planos` | Planos | view, edit |

**Simulación de roles:** `RoleSimulationMiddleware` (`roles/middleware.py`) permite a un usuario con rol `Administrador` o superusuario simular temporalmente los permisos de otro rol activo. Al activarse, parchea `request.user.has_perm_custom` en memoria durante ese request únicamente (no persiste en BD ni afecta a otros usuarios); se desactiva automáticamente si el rol simulado deja de existir o se desactiva.

---

## 7. Configuración del Proyecto

### `core/settings.py` — valores reales actuales (entorno de pruebas en VM, no producción)

```python
# Seguridad — ⚠️ valores de desarrollo, activos ahora mismo en la VM de pruebas
SECRET_KEY = 'django-insecure-...'   # Clave por defecto generada por Django, nunca rotada
DEBUG = True                          # Expone stacktraces completos (incluye SECRET_KEY y password de BD) ante cualquier error 500
ALLOWED_HOSTS = ['*']                 # Sin restricción de host

# Apps instaladas (8 apps propias)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',             # Gestión de usuarios
    'inspections',       # Cronograma + 5 módulos de inspección + áreas + reportes
    'roles',             # RBAC
    'notifications',     # Notificaciones internas
    'system_config',     # Configuración del sistema + catálogo de Planos
    'gestion_activos',   # Inventario de activos físicos
    'planos',            # Ubicación de activos en planos SVG
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'roles.middleware.RoleSimulationMiddleware',   # Debe ir después de AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Base de datos — PostgreSQL ACTIVA (no SQLite). Credenciales hardcodeadas en texto plano.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sst_db',
        'USER': 'app_plas',
        'PASSWORD': '...',   # hardcodeada en el archivo real — mover a variable de entorno
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
# El bloque de SQLite se dejó comentado en el archivo, solo como referencia para desarrollo local sin Postgres.

# Autenticación personalizada
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Sesiones: 30 minutos de inactividad
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Internacionalización
LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'

# Archivos estáticos y media
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# PK por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

> **Contexto actual:** el sistema corre en una VM dedicada a pruebas internas. La combinación `DEBUG=True` + `ALLOWED_HOSTS=['*']` + credenciales en texto plano no es urgente de corregir mientras el acceso esté controlado, pero son los tres puntos a resolver antes de cualquier exposición a usuarios externos o a internet (mover `SECRET_KEY` y credenciales de BD a variables de entorno, `DEBUG=False`, restringir `ALLOWED_HOSTS`).

### Variables de entorno recomendadas para producción

Para producción se recomienda mover los valores sensibles a variables de entorno. Usar `python-decouple` o `django-environ`:

```env
DJANGO_SECRET_KEY=tu-clave-secreta-real
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Base de datos PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sgsst_db
DB_USER=sgsst_user
DB_PASSWORD=password_seguro
DB_HOST=localhost
DB_PORT=5432

# Email (para notificaciones)
EMAIL_HOST=smtp.tuservidor.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@tudominio.com
EMAIL_HOST_PASSWORD=email_password
```

---

## 8. Dependencias y Librerías

### Dependencias de producción (`requirements.txt`)

| Librería | Versión | Propósito |
|---|---|---|
| `Django` | 5.2.7 | Framework web principal |
| `asgiref` | 3.10.0 | Soporte ASGI para Django |
| `sqlparse` | 0.5.3 | Parser SQL usado internamente por Django |
| `openpyxl` | 3.1.5 | Generación de archivos Excel (exportación de reportes) |
| `pandas` | 2.2.3 | Manipulación de datos para reportes |
| `numpy` | 2.2.3 | Dependencia de pandas |
| `python-dateutil` | 2.9.0 | Cálculo de fechas relativas y frecuencias de inspección |
| `pytz` | 2025.1 | Manejo de zonas horarias |
| `tzdata` | 2025.1 | Base de datos de zonas horarias |
| `psycopg` | 3.2.10 | Driver PostgreSQL (para producción) |
| `psycopg-binary` | 3.2.10 | Driver PostgreSQL binario |
| `pypdf` | 6.7.0 | Procesamiento de PDFs |
| `httpx` | 0.28.1 | Cliente HTTP asíncrono |
| `ollama` | 0.6.1 | Cliente para modelos de lenguaje locales |
| `pydantic` | 2.12.5 | Validación de datos |

### Librerías de frontend (CDN — no en requirements.txt)

| Librería | Propósito |
|---|---|
| **Chart.js** | Gráficos interactivos en el dashboard y módulo de reportes |
| **Font Awesome** | Iconografía |
| **Google Fonts (Inter)** | Tipografía del sistema |
| **Signature Pad** | Captura de firmas digitales en canvas |

---

## 9. Flujo de una Solicitud HTTP

El siguiente diagrama muestra el ciclo completo de vida de una solicitud HTTP dentro del sistema, usando como ejemplo `GET /inspections/forklift/` (lista de inspecciones de montacargas):

```
1. Cliente (Navegador)
   │  GET /inspections/forklift/
   │  Headers: Cookie: sessionid=xxx
   ▼

2. Django WSGI Server  (manage.py runserver / gunicorn)
   │
   ▼

3. Middleware Stack (en orden)
   ├── SecurityMiddleware        → Headers de seguridad
   ├── SessionMiddleware         → Carga sesión del cookie sessionid
   ├── CommonMiddleware          → Normalización de URLs
   ├── CsrfViewMiddleware        → Validación token CSRF (en POST)
   ├── AuthenticationMiddleware  → Asigna request.user desde sesión
   ├── MessageMiddleware         → Sistema de mensajes flash
   └── XFrameOptionsMiddleware   → Header X-Frame-Options
   │
   ▼

4. URL Dispatcher (core/urls.py)
   │  path('inspections/', include('inspections.urls'))
   │                              │
   │                              └── path('forklift/', ForkliftListView)
   ▼

5. RolePermissionRequiredMixin.dispatch()
   ├── request.user.is_authenticated? → Sí (sesión válida)
   └── user.has_perm_custom('forklift', 'view')? → Sí (rol Montacarguista)
   │
   ▼

6. ForkliftListView.get() (CBV)
   ├── get_queryset() → ForkliftInspection.objects.filter(...)
   ├── get_context_data()
   │     ├── object_list   (inspecciones filtradas/paginadas)
   │     ├── stats         (contadores: total, cerradas, vencidas)
   │     ├── monthly_stats (cumplimiento mensual para gráfico)
   │     └── filters       (áreas, tipos, estado)
   └── render(request, 'inspections/forklift_list.html', context)
   │
   ▼

7. Template Engine (DTL)
   ├── Extiende base.html
   ├── Renderiza sidebar, navbar con rol del usuario
   ├── Inserta datos del context en HTML
   └── Genera respuesta HTML completa
   │
   ▼

8. HTTP Response → Navegador
   Status: 200 OK
   Content-Type: text/html; charset=utf-8
```

### Flujo de un POST (crear inspección)

```
POST /inspections/forklift/add/
       │
       ├── CsrfViewMiddleware valida token
       ├── RolePermissionRequiredMixin verifica ('forklift', 'create')
       ├── ForkliftCreateView.post()
       │     ├── ForkliftInspectionForm(request.POST)
       │     ├── form.is_valid()
       │     │     ├── Validaciones de campos
       │     │     └── clean() custom si aplica
       │     ├── form.save() → INSERT INTO inspections_forkliftinspection
       │     └── redirect → forklift_detail/{pk}/
       │
       └── HTTP 302 Redirect → GET /inspections/forklift/{pk}/
```

---

## 10. Instalación y Despliegue

### 10.1 Requisitos previos

- Python 3.11 o superior
- pip
- Git
- (Producción) PostgreSQL 14+, Nginx, Gunicorn

---

### 10.2 Instalación en entorno de desarrollo

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-org/sgsst-inspections.git
cd sgsst-inspections

# 2. Crear y activar entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Inicializar permisos y roles del sistema (comandos de management reales)
python manage.py init_permissions
python manage.py init_roles
python manage.py init_areas

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Levantar servidor de desarrollo
python manage.py runserver
```

> Los scripts sueltos `setup_permissions.py`, `setup_reports_perm.py`, `init_system_config.py`, etc. en la raíz del proyecto son residuos de mantenimiento ad-hoc de iteraciones anteriores — usar siempre los comandos `manage.py` de arriba, que son los soportados y mantenidos.

Acceder en: `http://127.0.0.1:8000`

---

### 10.3 Creación de roles y permisos iniciales

```bash
# Sincronizar permisos en BD con PERMISSION_MATRIX (roles/models.py)
python manage.py init_permissions

# Crear la semilla de roles base
python manage.py init_roles
```

Los roles creados automáticamente son:

| Rol | Permisos |
|---|---|
| **Administrador** | Todos los módulos, todas las acciones (48 permisos) |
| **Equipo SST** | view, create, edit, details en todos los módulos |
| **Almacenista** | view, create, edit, details (uso previsto: almacenamiento) |
| **Brigadista** | view, create, edit, details (uso previsto: extintores y botiquines) |
| **Montacarguista** | view, create, details (uso previsto: montacargas) |
| **Consulta** | view, details (solo lectura) |

> Nota: `init_roles` asigna permisos por coincidencia de texto en el codename (`view`, `create`, etc.), no por módulo — en la práctica, a estos roles conviene ajustarles manualmente los módulos exactos desde la interfaz de Roles tras la instalación inicial.

---

### 10.4 Despliegue en producción (Linux + Nginx + Gunicorn)

#### Paso 1: Configurar variables de entorno

```bash
export DJANGO_SECRET_KEY='clave-super-segura-aleatoria'
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS='tudominio.com'
export DB_NAME='sgsst_db'
export DB_USER='sgsst_user'
export DB_PASSWORD='contraseña'
export DB_HOST='localhost'
```

#### Paso 2: Actualizar `settings.py` para producción

```python
import os

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### Paso 3: Preparar archivos estáticos y base de datos

```bash
python manage.py collectstatic --noinput
python manage.py migrate
```

#### Paso 4: Configurar Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar (en producción usar systemd service)
gunicorn core.wsgi:application \
    --workers 3 \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

#### Paso 5: Configurar Nginx

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location /static/ {
        alias /ruta/al/proyecto/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Paso 6: Configurar SSL (recomendado con Certbot)

```bash
sudo certbot --nginx -d tudominio.com
```

---

### 10.5 Comandos útiles de mantenimiento

```bash
# Limpiar sesiones expiradas
python manage.py clearsessions

# Crear backup de la base de datos (dumpdata funciona igual sobre PostgreSQL)
python manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission \
    --indent 2 > backup_$(date +%Y%m%d).json

# Restaurar backup
python manage.py loaddata backup_20260220.json

# Ver todas las rutas del sistema
python manage.py show_urls

# Verificar configuración sin errores
python manage.py check --deploy
```

---

## Notas de Seguridad para Producción

> ⚠️ **Estado actual: ninguno de estos puntos está aplicado todavía** — el sistema corre en una VM de pruebas internas con `DEBUG=True`, `ALLOWED_HOSTS=['*']` y credenciales de BD hardcodeadas. No es urgente para el entorno de pruebas actual, pero son requisito antes de cualquier exposición fuera de ese entorno controlado:

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` aleatoria, rotada y movida a variable de entorno (actualmente es la generada por defecto por Django)
- [ ] `ALLOWED_HOSTS` restringido al dominio/host real (actualmente `['*']`)
- [ ] Credenciales de PostgreSQL movidas a variables de entorno (actualmente en texto plano en `settings.py`)
- [ ] HTTPS habilitado (certificado SSL)
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] `collectstatic` ejecutado y servido por Nginx
- [ ] Backups automáticos configurados (hoy son manuales/ad-hoc)

---

*Documentación revisada el 23 de octubre de 2026, contrastando cada afirmación directamente contra el código fuente (settings.py, models.py, urls.py, mixins.py y comandos de management reales). Para volver a sincronizarla tras cambios futuros, repetir ese contraste en vez de editar de memoria.*
