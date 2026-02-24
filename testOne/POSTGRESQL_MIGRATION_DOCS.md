# Documentación Técnica: Configuración y Migración a PostgreSQL
## Proyecto SG-SST — Sistema de Gestión de Seguridad y Salud en el Trabajo

> **Versión:** Django 5.2.7 | **Motor de BD:** PostgreSQL | **Driver:** psycopg 3.x  
> **Fecha de generación:** 2026-02-23 | **Entorno:** Producción / Desarrollo

---

## Tabla de Contenidos

1. [Arquitectura del Proyecto](#1-arquitectura-del-proyecto)
2. [Configuración en settings.py](#2-configuración-en-settingspy)
3. [Requisitos del Entorno](#3-requisitos-del-entorno)
4. [Proceso de Migración Paso a Paso](#4-proceso-de-migración-paso-a-paso)
5. [Funcionamiento Interno de Django ORM](#5-funcionamiento-interno-de-django-orm)
6. [Estructura de Tablas Generadas](#6-estructura-de-tablas-generadas)
7. [Tablas del Proyecto SST](#7-tablas-del-proyecto-sst)
8. [Buenas Prácticas para Producción](#8-buenas-prácticas-para-producción)
9. [Manejo de Errores Comunes](#9-manejo-de-errores-comunes)
10. [Seguridad y Variables de Entorno](#10-seguridad-y-variables-de-entorno)

---

## 1. Arquitectura del Proyecto

El proyecto SST es una aplicación Django modular compuesta por **5 aplicaciones personalizadas**:

```
testOne/                          ← Directorio raíz del proyecto
├── core/                         ← Configuración central (settings, urls, wsgi)
│   └── settings.py
├── users/                        ← App: Gestión de usuarios (CustomUser)
│   └── migrations/ (3 archivos)
├── roles/                        ← App: Roles y permisos RBAC
│   └── migrations/ (3 archivos)
├── inspections/                  ← App: Módulo principal de inspecciones
│   └── migrations/ (24 archivos)
├── notifications/                ← App: Notificaciones internas
│   └── migrations/ (2 archivos)
├── system_config/                ← App: Configuración dinámica del sistema
│   └── migrations/ (2 archivos)
└── manage.py
```

**Relaciones entre aplicaciones:**

```
roles ──────────────────────────────────────────────────┐
  └── Permission (módulo + acción)                       │
  └── Role (agrupa permisos)                             │
                                                         ↓
users                                             users.CustomUser
  └── CustomUser (extiende AbstractUser)          (AUTH_USER_MODEL)
        └── FK → roles.Role                             ↑
                                                        │
inspections                                             │
  └── Area                                              │
  └── InspectionSchedule ──── FK → Area ────────── FK → users.CustomUser
  └── ExtinguisherInspection  (BaseInspection)
  └── FirstAidInspection      (BaseInspection)
  └── ProcessInspection       (BaseInspection)
  └── StorageInspection       (BaseInspection)
  └── ForkliftInspection      (BaseInspection)
  └── [CheckItems y Signatures por cada tipo]

notifications
  └── NotificationGroup ──── M2M → users.CustomUser
  └── Notification ────────── FK → users.CustomUser

system_config
  └── SystemConfig (clave → valor tipado)
```

---

## 2. Configuración en settings.py

### 2.1 Bloque DATABASES actual

```python
# core/settings.py — líneas 80-89

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sst_db',
        'USER': 'app_plas',
        'PASSWORD': '94#qS0',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2.2 Anatomía de cada parámetro

| Parámetro | Valor actual | Descripción técnica |
|-----------|-------------|---------------------|
| `ENGINE` | `django.db.backends.postgresql` | Indica a Django qué backend usar. Requiere el paquete `psycopg` (v3) o `psycopg2` (v2). |
| `NAME` | `sst_db` | Nombre de la base de datos PostgreSQL. Debe existir antes de ejecutar migraciones. |
| `USER` | `app_plas` | Rol de PostgreSQL con privilegios sobre `sst_db`. |
| `PASSWORD` | `94#qS0` | Contraseña del rol. **No debe estar en texto plano en producción.** Ver §10. |
| `HOST` | `localhost` | Dirección del servidor PostgreSQL. Puede ser IP, hostname o socket UNIX. |
| `PORT` | `5432` | Puerto TCP estándar de PostgreSQL. |

### 2.3 Parámetros opcionales recomendados para producción

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sst_db'),
        'USER': os.environ.get('DB_USER', 'app_plas'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,          # Timeout de conexión en segundos
            'sslmode': 'require',           # Exigir SSL en producción
        },
        'CONN_MAX_AGE': 60,                 # Reutilizar conexiones por 60 segundos
        'CONN_HEALTH_CHECKS': True,         # Verificar conexiones persistentes (Django 4.1+)
    }
}
```

### 2.4 Configuración de Internacionalización relevante

```python
# settings.py actuales
LANGUAGE_CODE = 'es'      # Idioma español — afecta mensajes de validación
TIME_ZONE = 'UTC'         # ⚠️ Considera cambiar a 'America/Bogota' para Colombia
USE_TZ = True             # Activa timezone-aware datetimes — IMPORTANTE para PostgreSQL
```

> **Nota importante:** Con `USE_TZ = True`, Django almacena todas las fechas en UTC en PostgreSQL usando el tipo `TIMESTAMP WITH TIME ZONE`. Esto garantiza consistencia global pero requiere conversión de zona horaria en las vistas.

---

## 3. Requisitos del Entorno

### 3.1 Software requerido

| Componente | Versión mínima | Versión en proyecto | Propósito |
|-----------|---------------|-------------------|-----------|
| Python | 3.10+ | (ver entorno virtual) | Lenguaje base |
| Django | 4.2+ | **5.2.7** | Framework web |
| PostgreSQL | 13+ | 14+ recomendado | Motor de base de datos |
| psycopg | 3.x | **3.2.10** | Driver Python para PostgreSQL |
| psycopg-binary | 3.x | **3.2.10** | Compilación binaria del driver |

> **Diferencia psycopg2 vs psycopg3:** El proyecto usa `psycopg` 3.x (paquete `psycopg`), la versión moderna. Es compatible con `django.db.backends.postgresql` de Django 4.2+. **No mezclar con psycopg2.**

### 3.2 Instalación del driver

```bash
# Opción A: psycopg 3 binario (usada en el proyecto — más fácil de instalar)
pip install "psycopg[binary]"

# Opción B: psycopg 3 con compilación nativa (más eficiente en producción)
pip install "psycopg[c]"

# Verificar instalación
python -c "import psycopg; print(psycopg.__version__)"
```

### 3.3 Instalación completa desde requirements.txt

```bash
pip install -r requirements.txt
```

**Paquetes clave en requirements.txt:**

```
Django==5.2.7          # Framework principal
psycopg==3.2.10        # Driver PostgreSQL v3
psycopg-binary==3.2.10 # Binarios del driver
openpyxl==3.1.5        # Exportación Excel (reportes)
pandas==2.2.3          # Análisis de datos
```

### 3.4 Preparación de PostgreSQL

```sql
-- Ejecutar como superusuario de PostgreSQL (psql -U postgres)

-- 1. Crear el usuario de aplicación
CREATE USER app_plas WITH PASSWORD '94#qS0';

-- 2. Crear la base de datos
CREATE DATABASE sst_db
    WITH OWNER = app_plas
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- 3. Otorgar privilegios completos
GRANT ALL PRIVILEGES ON DATABASE sst_db TO app_plas;

-- 4. Conectarse a sst_db y otorgar privilegios sobre el schema
\c sst_db
GRANT ALL ON SCHEMA public TO app_plas;
GRANT CREATE ON SCHEMA public TO app_plas;

-- 5. Verificar conexión
\c sst_db app_plas
```

---

## 4. Proceso de Migración Paso a Paso

### 4.1 Diagrama del proceso completo

```
[Modelos Python] 
      │
      ↓ python manage.py makemigrations
[Archivos .py en migrations/]
      │
      ↓ python manage.py migrate
[Tablas en sst_db (PostgreSQL)]
      │
      ↓ python manage.py createsuperuser
[Usuario admin en auth_user]
```

### 4.2 Paso 1 — Verificar conexión a PostgreSQL

```bash
# Desde el directorio raíz del proyecto
python manage.py dbshell

# Si la conexión falla, prueba directamente con psql:
psql -U app_plas -h localhost -p 5432 -d sst_db
```

### 4.3 Paso 2 — Verificar estado de migraciones

```bash
# Ver qué migraciones existen y cuáles ya fueron aplicadas
python manage.py showmigrations

# Salida esperada (ejemplo):
# admin
#   [X] 0001_initial
#   [X] 0002_logentry_remove_auto_add
# auth
#   [X] 0001_initial
#   [X] ...0012_alter_user_first_name_max_length
# inspections
#   [X] 0001_initial
#   [ ] 0002_... ← pendiente
```

### 4.4 Paso 3 — Generar nuevas migraciones (si hay cambios en modelos)

```bash
# Detectar cambios en TODOS los modelos
python manage.py makemigrations

# Detectar cambios en una app específica
python manage.py makemigrations inspections
python manage.py makemigrations users
python manage.py makemigrations roles
python manage.py makemigrations notifications
python manage.py makemigrations system_config

# Ver el SQL que generaría una migración (sin ejecutarla)
python manage.py sqlmigrate inspections 0001_initial
```

### 4.5 Paso 4 — Aplicar migraciones en orden correcto

```bash
# Aplicar TODAS las migraciones pendientes (orden automático por dependencias)
python manage.py migrate

# Orden real que Django resuelve internamente:
# 1. contenttypes (base del sistema de tipos)
# 2. auth (autenticación base)
# 3. roles (usuarios dependen de roles)
# 4. users (extiende auth, depende de roles)
# 5. inspections (depende de users)
# 6. notifications (depende de users)
# 7. system_config (independiente)
# 8. admin (depende de auth + contenttypes)
# 9. sessions (independiente)
```

### 4.6 Paso 5 — Verificar que todo fue aplicado

```bash
python manage.py showmigrations
# Todos deben aparecer con [X]

# Verificar tablas en PostgreSQL
python manage.py dbshell
# Dentro de psql:
\dt
# Lista todas las tablas. Debe haber ~45+ tablas.
```

### 4.7 Paso 6 — Crear superusuario

```bash
python manage.py createsuperuser
# Solicita: email (campo USERNAME_FIELD), username, first_name, last_name, password
# ⚠️ El proyecto usa email como campo de login (USERNAME_FIELD = 'email')
```

### 4.8 Paso 7 — Cargar datos iniciales (fixtures opcionales)

```bash
# Inicializar configuración del sistema
python init_system_config.py

# Configurar permisos base del sistema RBAC
python setup_permissions.py

# Configurar permisos de reportes
python setup_reports_perm.py
```

---

## 5. Funcionamiento Interno de Django ORM

### 5.1 ¿Qué hace `makemigrations`?

Cuando ejecutas `python manage.py makemigrations`, Django:

1. **Importa todos los modelos** de cada `INSTALLED_APPS`
2. **Compara el estado actual** de los modelos con el último estado guardado en los archivos `migrations/`
3. **Detecta diferencias**: campos nuevos, eliminados, renombrados, cambios de tipo
4. **Genera un archivo Python** con operaciones de migración ordenadas

```python
# Ejemplo real: inspections/migrations/0009_area.py (simplificado)
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0008_forkliftinspection_forkliftcheckitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),        # DEFAULT_AUTO_FIELD = BigAutoField
                ('name', models.CharField(max_length=200, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
```

### 5.2 ¿Qué hace `migrate`?

Cuando ejecutas `python manage.py migrate`, Django:

1. **Lee la tabla `django_migrations`** (se crea automáticamente) para saber qué ya fue aplicado
2. **Resuelve el grafo de dependencias** entre migraciones (mediante `dependencies = [...]`)
3. **Ejecuta cada migración pendiente** en una transacción SQL
4. **Registra la migración aplicada** en `django_migrations`

```sql
-- Transacción típica que ejecuta Django por cada migración:
BEGIN;
  CREATE TABLE "inspections_area" (
    "id" bigserial NOT NULL PRIMARY KEY,
    "name" varchar(200) NOT NULL UNIQUE,
    "is_active" boolean NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL
  );
  INSERT INTO "django_migrations" ("app", "name", "applied")
  VALUES ('inspections', '0009_area', NOW());
COMMIT;
```

### 5.3 Tipos de operaciones de migración

| Operación Django | SQL generado en PostgreSQL |
|-----------------|---------------------------|
| `CreateModel` | `CREATE TABLE` |
| `DeleteModel` | `DROP TABLE` |
| `AddField` | `ALTER TABLE ... ADD COLUMN` |
| `RemoveField` | `ALTER TABLE ... DROP COLUMN` |
| `AlterField` | `ALTER TABLE ... ALTER COLUMN TYPE` |
| `AddIndex` | `CREATE INDEX` |
| `AddConstraint` | `ALTER TABLE ... ADD CONSTRAINT` |
| `RunSQL` | SQL arbitrario |

---

## 6. Estructura de Tablas Generadas Automáticamente

### 6.1 Tablas de Django Framework (apps del core)

#### `django_migrations` — Registro de migraciones
```sql
CREATE TABLE django_migrations (
    id          bigserial PRIMARY KEY,
    app         varchar(255) NOT NULL,   -- 'inspections', 'users', etc.
    name        varchar(255) NOT NULL,   -- '0001_initial'
    applied     timestamp with time zone NOT NULL
);
```

#### `django_content_types` — Sistema de tipos genéricos
```sql
CREATE TABLE django_content_types (
    id         serial PRIMARY KEY,
    app_label  varchar(100) NOT NULL,
    model      varchar(100) NOT NULL,
    UNIQUE (app_label, model)
);
```

#### `auth_permission` — Permisos estándar de Django
```sql
CREATE TABLE auth_permission (
    id              serial PRIMARY KEY,
    name            varchar(255) NOT NULL,
    content_type_id integer NOT NULL REFERENCES django_content_types(id),
    codename        varchar(100) NOT NULL,
    UNIQUE (content_type_id, codename)
);
```

#### `auth_group` — Grupos de Django (sin uso directo en este proyecto)
```sql
CREATE TABLE auth_group (
    id   serial PRIMARY KEY,
    name varchar(150) NOT NULL UNIQUE
);

CREATE TABLE auth_group_permissions (
    id            bigserial PRIMARY KEY,
    group_id      integer REFERENCES auth_group(id),
    permission_id integer REFERENCES auth_permission(id),
    UNIQUE (group_id, permission_id)
);
```

#### `users_customuser` — Usuarios del sistema (CustomUser)
```sql
CREATE TABLE users_customuser (
    id               bigserial PRIMARY KEY,
    password         varchar(128) NOT NULL,
    last_login       timestamp with time zone,
    is_superuser     boolean NOT NULL DEFAULT false,
    username         varchar(150) NOT NULL UNIQUE,
    first_name       varchar(150) NOT NULL DEFAULT '',
    last_name        varchar(150) NOT NULL DEFAULT '',
    is_staff         boolean NOT NULL DEFAULT false,
    is_active        boolean NOT NULL DEFAULT true,
    date_joined      timestamp with time zone NOT NULL,
    email            varchar(254) NOT NULL UNIQUE,  -- USERNAME_FIELD
    document_number  varchar(20),
    updated_at       timestamp with time zone NOT NULL,
    digital_signature text,                          -- Base64 encoded image
    role_id          bigint REFERENCES roles_role(id) ON DELETE SET NULL
);
```

#### `django_session` — Sesiones de usuario
```sql
CREATE TABLE django_session (
    session_key  varchar(40) PRIMARY KEY,
    session_data text NOT NULL,           -- Datos serializados (JSON+base64)
    expire_date  timestamp with time zone NOT NULL
);
-- Índice automático:
CREATE INDEX django_session_expire_date ON django_session (expire_date);
```

> **Configuración de sesión en el proyecto:**
> ```python
> SESSION_COOKIE_AGE = 1800              # Expira en 30 minutos de inactividad
> SESSION_SAVE_EVERY_REQUEST = True      # Resetea el timer en cada petición
> SESSION_EXPIRE_AT_BROWSER_CLOSE = True # Cierra sesión al cerrar el navegador
> ```

#### `django_admin_log` — Log de acciones del admin
```sql
CREATE TABLE django_admin_log (
    id              serial PRIMARY KEY,
    action_time     timestamp with time zone NOT NULL,
    object_id       text,
    object_repr     varchar(200) NOT NULL,
    action_flag     smallint NOT NULL,  -- 1=add, 2=change, 3=delete
    change_message  text NOT NULL,
    content_type_id integer REFERENCES django_content_types(id),
    user_id         bigint NOT NULL REFERENCES users_customuser(id)
);
```

---

## 7. Tablas del Proyecto SST

### 7.1 App: `roles`

#### `roles_permission` — Permisos granulares RBAC
```sql
CREATE TABLE roles_permission (
    id          bigserial PRIMARY KEY,
    module      varchar(50) NOT NULL,   -- 'users', 'inspections', 'forklift', etc.
    action      varchar(20) NOT NULL,   -- 'view', 'create', 'edit', 'delete'
    codename    varchar(100) NOT NULL UNIQUE,
    description varchar(255) NOT NULL,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamp with time zone NOT NULL,
    UNIQUE (module, action)
);
```

**Módulos disponibles:** `users`, `inspections`, `schedule`, `extinguisher`, `first_aid`, `process`, `storage`, `forklift`, `roles`, `reports`

#### `roles_role` — Roles del sistema
```sql
CREATE TABLE roles_role (
    id             bigserial PRIMARY KEY,
    name           varchar(100) NOT NULL UNIQUE,
    description    text NOT NULL DEFAULT '',
    is_active      boolean NOT NULL DEFAULT true,
    is_system_role boolean NOT NULL DEFAULT false,
    created_at     timestamp with time zone NOT NULL,
    updated_at     timestamp with time zone NOT NULL
);
```

#### `roles_role_permissions` — Tabla intermedia Role↔Permission (M2M)
```sql
CREATE TABLE roles_role_permissions (
    id            bigserial PRIMARY KEY,
    role_id       bigint NOT NULL REFERENCES roles_role(id),
    permission_id bigint NOT NULL REFERENCES roles_permission(id),
    UNIQUE (role_id, permission_id)
);
```

### 7.2 App: `users`

#### `users_customuser_groups` y `users_customuser_user_permissions`
Tablas intermedias M2M heredadas de `AbstractUser`:
```sql
CREATE TABLE users_customuser_groups (
    id            bigserial PRIMARY KEY,
    customuser_id bigint REFERENCES users_customuser(id),
    group_id      integer REFERENCES auth_group(id)
);

CREATE TABLE users_customuser_user_permissions (
    id            bigserial PRIMARY KEY,
    customuser_id bigint REFERENCES users_customuser(id),
    permission_id integer REFERENCES auth_permission(id)
);
```

### 7.3 App: `inspections`

#### `inspections_area` — Áreas de la organización
```sql
CREATE TABLE inspections_area (
    id         bigserial PRIMARY KEY,
    name       varchar(200) NOT NULL UNIQUE,
    is_active  boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);
```

#### `inspections_inspectionschedule` — Cronograma de inspecciones
```sql
CREATE TABLE inspections_inspectionschedule (
    id              bigserial PRIMARY KEY,
    year            integer,
    inspection_type varchar(200) NOT NULL,
    frequency       varchar(20) NOT NULL,      -- 'Mensual','Bimestral','Anual'...
    scheduled_date  date NOT NULL,
    status          varchar(20) NOT NULL DEFAULT 'Programada',
    observations    text,
    created_at      timestamp with time zone NOT NULL,
    updated_at      timestamp with time zone NOT NULL,
    area_id         bigint NOT NULL REFERENCES inspections_area(id) ON DELETE PROTECT,
    responsible_id  bigint REFERENCES users_customuser(id) ON DELETE CASCADE
);
```

#### Tablas de inspecciones específicas (heredan de `BaseInspection`)

Cada tipo de inspección genera su propia tabla. Todas comparten la estructura base:

```sql
-- Patrón común para: extinguisher, firstaid, process, storage, forklift
CREATE TABLE inspections_[tipo]inspection (
    id               bigserial PRIMARY KEY,
    inspection_date  date NOT NULL,
    observations     text NOT NULL DEFAULT '',
    status           varchar(30) NOT NULL DEFAULT 'Pendiente',
    created_at       timestamp with time zone NOT NULL,
    updated_at       timestamp with time zone NOT NULL,
    area_id          bigint REFERENCES inspections_area(id),
    inspector_id     bigint REFERENCES users_customuser(id),
    schedule_item_id bigint REFERENCES inspections_inspectionschedule(id),
    -- Campos específicos por tipo (inspector_role, forklift_type, etc.)
    additional_observations text,
    parent_inspection_id bigint REFERENCES inspections_[tipo]inspection(id) ON DELETE CASCADE
);
```

**Tablas generadas:**
- `inspections_extinguisherinspection` + `inspections_extinguisheritem` + `inspections_inspectionsignature`
- `inspections_firstaidinspection` + `inspections_firstaiditem` + `inspections_firstaidsignature`
- `inspections_processinspection` + `inspections_processcheckitem` + `inspections_processsignature`
- `inspections_storageinspection` + `inspections_storagecheckitem` + `inspections_storagesignature`
- `inspections_forkliftinspection` + `inspections_forkliftcheckitem` + `inspections_forkliftsignature`

### 7.4 App: `notifications`

```sql
CREATE TABLE notifications_notificationgroup (
    id                bigserial PRIMARY KEY,
    name              varchar(100) NOT NULL UNIQUE,
    description       text NOT NULL DEFAULT '',
    is_active         boolean NOT NULL DEFAULT true,
    is_system_default boolean NOT NULL DEFAULT false
);

CREATE TABLE notifications_notificationgroup_users (
    id                  bigserial PRIMARY KEY,
    notificationgroup_id bigint REFERENCES notifications_notificationgroup(id),
    customuser_id       bigint REFERENCES users_customuser(id)
);

CREATE TABLE notifications_notification (
    id                bigserial PRIMARY KEY,
    title             varchar(200) NOT NULL,
    message           text NOT NULL,
    link              varchar(255),
    notification_type varchar(20) NOT NULL DEFAULT 'system',
    is_read           boolean NOT NULL DEFAULT false,
    created_at        timestamp with time zone NOT NULL,
    user_id           bigint NOT NULL REFERENCES users_customuser(id) ON DELETE CASCADE
);
```

### 7.5 App: `system_config`

```sql
CREATE TABLE system_config_systemconfig (
    id          bigserial PRIMARY KEY,
    key         varchar(100) NOT NULL UNIQUE,
    value       varchar(255) NOT NULL,
    description text NOT NULL DEFAULT '',
    config_type varchar(20) NOT NULL DEFAULT 'string',  -- 'string','number','boolean'
    category    varchar(50) NOT NULL DEFAULT 'general',
    is_editable boolean NOT NULL DEFAULT true,
    updated_at  timestamp with time zone NOT NULL
);
```

### 7.6 Resumen de todas las tablas por app

| App | Tablas generadas | Total |
|-----|-----------------|-------|
| `django` (framework) | `django_migrations`, `django_content_types`, `django_session`, `django_admin_log` | 4 |
| `auth` | `auth_permission`, `auth_group`, `auth_group_permissions` | 3 |
| `users` | `users_customuser`, `users_customuser_groups`, `users_customuser_user_permissions` | 3 |
| `roles` | `roles_permission`, `roles_role`, `roles_role_permissions` | 3 |
| `inspections` | Area, InspectionSchedule, 5×(Inspection + CheckItem + Signature) = 17 tablas | 17 |
| `notifications` | NotificationGroup, NotificationGroup_users, Notification | 3 |
| `system_config` | SystemConfig | 1 |
| **Total** | | **~34 tablas** |

---

## 8. Buenas Prácticas para Producción con PostgreSQL

### 8.1 Configuración de conexiones persistentes

```python
# settings.py — Producción
DATABASES = {
    'default': {
        ...
        'CONN_MAX_AGE': 60,          # Reutilizar conexiones hasta 60 segundos
        'CONN_HEALTH_CHECKS': True,  # Verificar que la conexión sigue viva (Django 4.1+)
    }
}
```

> **Por qué importa:** Por defecto, Django abre y cierra una conexión por cada petición HTTP. Con `CONN_MAX_AGE > 0`, la conexión se reutiliza durante `N` segundos, reduciendo latencia y carga en el servidor PostgreSQL.

### 8.2 Usar índices en campos de búsqueda frecuente

```python
# En los modelos donde hagas filtros frecuentes:
class InspectionSchedule(models.Model):
    status = models.CharField(max_length=20, db_index=True)      # Filtro frecuente
    scheduled_date = models.DateField(db_index=True)              # Ordenamiento
    area = models.ForeignKey('Area', on_delete=models.PROTECT)    # FK ya indexada
```

### 8.3 Configuración PostgreSQL recomendada (postgresql.conf)

```ini
# /etc/postgresql/14/main/postgresql.conf

# Memoria
shared_buffers = 256MB          # 25% de RAM disponible
work_mem = 16MB                 # Memoria por operación de ordenamiento
maintenance_work_mem = 64MB     # Para VACUUM, CREATE INDEX

# Conexiones
max_connections = 100           # Django + workers + herramientas admin
connection_limit = 90           # Reservar 10 para admin

# Logging (para diagnóstico)
log_min_duration_statement = 1000   # Loguear queries > 1 segundo
log_line_prefix = '%t [%p]: [%l-1] '
```

### 8.4 Crear backups regulares

```bash
# Backup completo de sst_db
pg_dump -U app_plas -h localhost -d sst_db -F c -f backup_sst_$(date +%Y%m%d).dump

# Restaurar
pg_restore -U postgres -h localhost -d sst_db backup_sst_20260223.dump

# Automatizar con cron (Linux/macOS):
# 0 2 * * * pg_dump -U app_plas -d sst_db -F c -f /backups/sst_$(date +\%Y\%m\%d).dump
```

### 8.5 Usar transacciones atómicas en vistas críticas

```python
# views.py — Para operaciones que modifican múltiples tablas
from django.db import transaction

@transaction.atomic
def crear_inspeccion(request):
    inspeccion = ForkliftInspection.objects.create(...)
    for item in items:
        ForkliftCheckItem.objects.create(inspection=inspeccion, ...)
    # Si falla cualquier línea, TODO se revierte automáticamente
```

---

## 9. Manejo de Errores Comunes

### 9.1 `OperationalError: could not connect to server`

**Causa:** PostgreSQL no está corriendo o la dirección/puerto son incorrectos.

```bash
# Diagnóstico en Windows:
Get-Service -Name postgresql*
Start-Service postgresql-x64-14

# Diagnóstico en Linux:
sudo systemctl status postgresql
sudo systemctl start postgresql

# Verificar que escucha en el puerto correcto:
netstat -an | findstr 5432   # Windows
ss -tlnp | grep 5432         # Linux
```

### 9.2 `OperationalError: password authentication failed for user "app_plas"`

**Causa:** Contraseña incorrecta o el usuario no existe en PostgreSQL.

```sql
-- Verificar que el usuario existe
\du app_plas

-- Cambiar contraseña
ALTER USER app_plas WITH PASSWORD 'nueva_contraseña';

-- Verificar pg_hba.conf (método de autenticación)
-- /etc/postgresql/14/main/pg_hba.conf
-- La línea para localhost debe incluir:
-- host  all  all  127.0.0.1/32  md5
```

### 9.3 `django.db.utils.ProgrammingError: relation "X" does not exist`

**Causa:** Las migraciones no han sido aplicadas o hay una migración corrupta.

```bash
# Verificar estado de migraciones
python manage.py showmigrations

# Aplicar migraciones pendientes
python manage.py migrate

# Si el problema persiste — verificar integridad del grafo de migraciones
python manage.py migrate --check
```

### 9.4 `InconsistentMigrationHistory`

**Causa:** La tabla `django_migrations` tiene registros que no coinciden con los archivos reales.

```bash
# Ver qué hay en django_migrations
python manage.py dbshell
SELECT app, name, applied FROM django_migrations ORDER BY app, name;

# Opción nuclear (solo en desarrollo): resetear migraciones
# ⚠️ ELIMINA TODOS LOS DATOS
python manage.py migrate --run-syncdb
```

### 9.5 `ModuleNotFoundError: No module named 'psycopg'`

**Causa:** El driver no está instalado en el entorno virtual activo.

```bash
# Verificar que el virtualenv está activo
where python    # Windows
which python    # Linux/macOS

# Instalar driver
pip install "psycopg[binary]"

# O reinstalar todo el proyecto
pip install -r requirements.txt
```

### 9.6 `permission denied for schema public`

**Causa:** En PostgreSQL 15+, el schema `public` ya no es accesible por defecto para nuevos usuarios.

```sql
-- Ejecutar como superusuario en sst_db
GRANT CREATE ON SCHEMA public TO app_plas;
GRANT USAGE ON SCHEMA public TO app_plas;

-- Para dar acceso a todas las tablas existentes:
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_plas;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_plas;
```

### 9.7 `DataError: value too long for type character varying(N)`

**Causa:** Los datos migrados desde SQLite exceden el `max_length` definido en el modelo.

```python
# Ver qué campo está fallando en el traceback
# Aumentar el max_length en el modelo:
class Area(models.Model):
    name = models.CharField(max_length=300)  # Era 200

# Regenerar migración:
python manage.py makemigrations inspections --name "increase_area_name_length"
python manage.py migrate
```

---

## 10. Seguridad y Variables de Entorno

### 10.1 Problema actual: credenciales en texto plano

```python
# ❌ CONFIGURACIÓN ACTUAL — INSEGURA PARA PRODUCCIÓN
SECRET_KEY = 'django-insecure-v+454x*vul6syum*dh@a2(k!fh4j!kijz@-6msg84cwh&iy(u5'
DATABASES = {
    'default': {
        'PASSWORD': '94#qS0',   # ← Visible en repositorio git
    }
}
```

### 10.2 Solución recomendada: python-decouple o django-environ

#### Opción A: `python-decouple` (recomendado)

```bash
pip install python-decouple
```

```ini
# .env — en la raíz del proyecto (NUNCA commitearlo en git)
SECRET_KEY=django-insecure-v+454x*vul6syum*dh@a2(k!fh4j!kijz@-6msg84cwh&iy(u5
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=sst_db
DB_USER=app_plas
DB_PASSWORD=94#qS0
DB_HOST=localhost
DB_PORT=5432
```

```python
# settings.py — Versión segura
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='sst_db'),
        'USER': config('DB_USER', default='app_plas'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

#### Opción B: Variables de entorno del sistema operativo

```powershell
# Windows PowerShell — configuración temporal
$env:DB_PASSWORD = "94#qS0"
$env:SECRET_KEY = "tu-clave-secreta-aqui"

# Windows — configuración permanente (para el usuario actual)
[System.Environment]::SetEnvironmentVariable("DB_PASSWORD", "94#qS0", "User")
```

```python
# settings.py — Usando os.environ
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sst_db'),
        'USER': os.environ.get('DB_USER', 'app_plas'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### 10.3 Archivo `.gitignore` obligatorio

```gitignore
# .gitignore — Agregar en la raíz del proyecto
.env
*.env
.env.local
.env.production
db.sqlite3
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
staticfiles/
media/
```

### 10.4 Configuración de seguridad de producción en settings.py

```python
# settings.py — PRODUCCIÓN SOLAMENTE
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com']

# HTTPS y cookies seguras
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Base de datos con SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
        },
        ...
    }
}
```

### 10.5 Permisos mínimos del usuario de base de datos

En producción, el usuario `app_plas` debe tener **solo los privilegios necesarios**:

```sql
-- Privilegios mínimos requeridos por Django
GRANT CONNECT ON DATABASE sst_db TO app_plas;
GRANT USAGE ON SCHEMA public TO app_plas;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_plas;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_plas;

-- Asegurarse que los futuros objetos también tengan permisos
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_plas;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_plas;

-- ❌ NO otorgar estos privilegios en producción:
-- GRANT SUPERUSER TO app_plas;
-- GRANT CREATEDB TO app_plas;
-- GRANT ALL PRIVILEGES ON DATABASE sst_db TO app_plas;
```

---

## Apéndice: Comandos de Referencia Rápida

```bash
# ── Migraciones ──────────────────────────────────────────────
python manage.py makemigrations                    # Detectar cambios
python manage.py makemigrations inspections        # App específica
python manage.py showmigrations                    # Ver estado
python manage.py sqlmigrate inspections 0001       # Ver SQL
python manage.py migrate                           # Aplicar todo
python manage.py migrate inspections 0005          # Migrar hasta versión específica
python manage.py migrate inspections zero          # Revertir todas las migraciones de una app

# ── Base de datos ─────────────────────────────────────────────
python manage.py dbshell                           # Abrir psql conectado a sst_db
python manage.py inspectdb                         # Generar modelos desde BD existente
python manage.py flush                             # Limpiar datos (mantiene tablas)

# ── Usuarios ──────────────────────────────────────────────────
python manage.py createsuperuser                   # Crear admin (usa email como login)
python manage.py changepassword admin@ejemplo.com  # Cambiar contraseña

# ── Verificación ──────────────────────────────────────────────
python manage.py check                             # Verificar configuración del proyecto
python manage.py check --database default          # Verificar configuración de BD
python manage.py validate_templates                # Verificar templates

# ── Servidor de desarrollo ────────────────────────────────────
python manage.py runserver                         # Puerto 8000
python manage.py runserver 0.0.0.0:8080           # Puerto personalizado + acceso externo
```

---

*Documentación generada automáticamente el 2026-02-23 para el proyecto SG-SST.*  
*Motor: Django 5.2.7 | Base de datos: PostgreSQL | Driver: psycopg 3.2.10*
