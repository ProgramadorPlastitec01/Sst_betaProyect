# 📋 Documentación Técnica — Sistema de Gestión de Inspecciones SG-SST

> **Versión:** 1.0.0  
> **Framework:** Django 5.2.7  
> **Base de datos:** SQLite 3 (desarrollo) / PostgreSQL (producción recomendada)  
> **Lenguaje:** Python 3.13  
> **Fecha:** Febrero 2026

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
| **Usuarios** | Gestión de usuarios con autenticación por email |
| **Roles y Permisos** | Control de acceso granular por módulo y acción (RBAC) |
| **Notificaciones** | Alertas internas con clasificación por tipo |
| **Configuración** | Parámetros del sistema editables desde la interfaz |

### Usuarios del sistema

El sistema emplea autenticación basada en **email** (no en username) y gestiona cuatro roles predefinidos:

- **Administrador** — Acceso total a todos los módulos
- **Inspector** — Registra y ejecuta inspecciones
- **Supervisor** — Visualiza y aprueba inspecciones
- **Visor** — Acceso de solo lectura al cronograma y reportes

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
testOne/                          ← Raíz del proyecto
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
│   └── templates/users/          ← Templates de usuarios
│
├── roles/                        ← App de Roles y Permisos (RBAC)
│   ├── models.py                 ← Role, Permission
│   ├── mixins.py                 ← RolePermissionRequiredMixin
│   ├── views.py                  ← CRUD de roles y asignación de permisos
│   ├── urls.py                   ← Rutas de /roles/
│   └── templates/roles/          ← Templates de roles
│
├── inspections/                  ← App principal de inspecciones
│   ├── models.py                 ← Todos los modelos de inspección
│   ├── views.py                  ← Todas las vistas de inspección (~2200 líneas)
│   ├── area_views.py             ← CRUD de Áreas
│   ├── forms.py                  ← Formularios de inspección
│   ├── urls.py                   ← Rutas de /inspections/
│   └── templates/inspections/    ← Templates de inspecciones
│
├── notifications/                ← App de notificaciones internas
│   ├── models.py                 ← NotificationGroup, Notification
│   ├── views.py                  ← Vistas de notificaciones
│   └── urls.py                   ← Rutas de /notifications/
│
├── system_config/                ← App de configuración del sistema
│   ├── models.py                 ← SystemConfig (clave-valor tipado)
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
├── db.sqlite3                    ← Base de datos SQLite (desarrollo)
└── TECHNICAL_DOCS.md             ← Este documento
```

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

Implementa un sistema de permisos granular propio, independiente del sistema nativo de Django.

**Responsabilidades:**
- Definir **módulos** (users, inspections, schedule, extinguisher, etc.) y **acciones** (view, create, edit, delete)
- Agrupar permisos en **Roles** (`Administrador`, `Inspector`, `Supervisor`, `Visor`)
- Exponer `RolePermissionRequiredMixin` para proteger vistas
- CRUD de roles desde la interfaz web

**Ruta base:** `/roles/`

---

### 4.4 `inspections` — Módulo Principal de Inspecciones

La app más grande del sistema. Gestiona el ciclo completo de vida de las inspecciones.

**Responsabilidades:**
- **Cronograma anual** (`InspectionSchedule`): planificación por módulo, área, frecuencia y responsable
- **5 módulos de inspección** con checklist, firmas digitales y reportes PDF-ready:
  - Extintores, Botiquines, Procesos, Almacenamiento, Montacargas
- **Gestión de Áreas** (`Area`): catálogo centralizado compartido
- **Módulo de Reportes**: vista consolidada con estadísticas, filtros avanzados, gráfico de tendencia mensual y exportación a Excel
- Soporte para **inspecciones de seguimiento** (follow-up) anidadas

**Ruta base:** `/inspections/`

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

Almacén de parámetros de configuración en formato clave-valor.

**Responsabilidades:**
- Persistir configuraciones editables (nombre de empresa, logo, etc.)
- Tipado de valores: `string`, `number`, `boolean`
- Agrupación por categoría
- Acceso programático vía `SystemConfig.get_value(key, default)`

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

**Módulos protegibles:**

| Código | Nombre visible |
|---|---|
| `users` | Usuarios |
| `inspections` | Cronograma |
| `extinguisher` | Extintores |
| `first_aid` | Botiquines |
| `process` | Procesos |
| `storage` | Almacenamiento |
| `forklift` | Montacargas |
| `roles` | Roles |
| `reports` | Reportes |

---

## 7. Configuración del Proyecto

### `core/settings.py`

```python
# Módulo de ajustes
DJANGO_SETTINGS_MODULE = 'core.settings'

# Seguridad
SECRET_KEY = '...'          # ⚠️ Cambiar en producción
DEBUG = True                # ⚠️ False en producción
ALLOWED_HOSTS = []          # ⚠️ Agregar dominio en producción

# Apps instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',           # Gestión de usuarios
    'inspections',     # Módulo principal de inspecciones
    'roles',           # RBAC
    'notifications',   # Notificaciones internas
    'system_config',   # Configuración del sistema
]

# Base de datos (SQLite en desarrollo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

# Archivos estáticos
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# PK por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

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
   └── user.has_perm_custom('forklift', 'view')? → Sí (rol Inspector)
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

# 5. Inicializar permisos del sistema
python setup_permissions.py
python setup_reports_perm.py

# 6. Inicializar configuración del sistema
python init_system_config.py

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Levantar servidor de desarrollo
python manage.py runserver
```

Acceder en: `http://127.0.0.1:8000`

---

### 10.3 Creación de roles y permisos iniciales

Después de la instalación, ejecutar desde Django shell o usando los scripts provistos:

```bash
# Inicializar todos los permisos y roles del sistema
python setup_permissions.py

# Agregar permisos del módulo de reportes
python setup_reports_perm.py
```

Los roles creados automáticamente son:

| Rol | Permisos |
|---|---|
| **Administrador** | Todos los módulos, todas las acciones |
| **Inspector** | view + create en inspecciones propias |
| **Supervisor** | view en todos los módulos |
| **Visor** | view en cronograma y reportes |

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

# Crear backup de la base de datos SQLite
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

> ⚠️ **Antes de desplegar en producción, verificar:**

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` aleatoria y no expuesta en el código fuente
- [ ] `ALLOWED_HOSTS` restringido al dominio real
- [ ] Base de datos PostgreSQL (no SQLite)
- [ ] HTTPS habilitado (certificado SSL)
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] Variables sensibles en variables de entorno (no en `settings.py`)
- [ ] `collectstatic` ejecutado y servido por Nginx
- [ ] Backups automáticos configurados

---

*Documentación generada el 20 de febrero de 2026. Para actualizar este documento, ejecutar el análisis del proyecto y regenerar según los cambios realizados.*
