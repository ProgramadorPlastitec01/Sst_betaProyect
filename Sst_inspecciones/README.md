# 🛡️ Sistema de Gestión SST - Plastitec

Sistema integral de Seguridad y Salud en el Trabajo (SST): cronograma e inspecciones, registro de activos físicos, ubicación en planos y control de acceso basado en roles (RBAC) propio.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.13+
- Django 5.2.7
- **PostgreSQL** (base de datos activa — ver nota abajo)

> ⚠️ El proyecto está configurado para conectarse a PostgreSQL (`core/settings.py`), no a SQLite. El archivo `db.sqlite3` en la raíz es un remanente de una etapa anterior y no está en uso. Si vas a correr el proyecto localmente sin Postgres, comenta el bloque `DATABASES` de Postgres y descomenta el bloque SQLite que ya está dejado como referencia en `settings.py`.

### Instalación

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd testOne

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Inicializar permisos y roles (en este orden)
python manage.py init_permissions
python manage.py init_roles
python manage.py init_areas

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Iniciar servidor
python manage.py runserver
```

### Acceso
- **URL:** http://127.0.0.1:8000
- **Admin:** http://127.0.0.1:8000/admin

---

## 📋 Módulos del Sistema

### 1. Autenticación y Usuarios
- Login/Logout (autenticación por **email**, no por username)
- Gestión de usuarios
- Firma digital (base64) por usuario
- Asignación de roles

### 2. Inspecciones (`/inspections/`)
- **Cronograma Anual** - Planificación de inspecciones, generación automática de la siguiente ocurrencia según frecuencia
- **Extintores** - Control de extintores
- **Botiquines** - Inspección de primeros auxilios
- **Procesos** - Inspección de instalaciones
- **Almacenamiento** - Control de almacenes
- **Montacargas** - Inspección de equipos
- **Áreas** - Catálogo centralizado de áreas, compartido por todos los módulos
- **Reportes** - Vista consolidada con estadísticas, filtros y exportación a Excel
- **Evidencias** - Carga de imágenes asociadas a cualquier inspección o ítem

### 3. Gestión de Activos (`/activos/`) ⭐
Inventario de activos físicos (extintores, montacargas, botiquines) independiente del checklist de inspección:
- Ficha por activo con datos específicos según su tipo
- Estado calculado automáticamente (vencido, próximo a vencer, en mantenimiento, etc.)
- Historial de movimientos (salida, reemplazo con temporal, retorno, baja) — registro histórico, nunca se elimina

### 4. Planos (`/planos/`) ⭐
Ubicación visual de activos sobre planos SVG, con historial de posiciones.

### 5. Roles y Permisos — RBAC (`/roles/`)
- Gestión de roles y permisos, totalmente dinámica (sin roles hardcodeados salvo "Administrador")
- Simulación de rol: un Administrador puede "probar" la interfaz con los permisos de otro rol sin modificar la base de datos
- Control de acceso aplicado en las vistas (ver sección RBAC)

### 6. Configuración del Sistema (`/configuration/`)
- Parámetros clave-valor editables desde la interfaz
- Catálogo de Planos

### 7. Notificaciones (`/notifications/`)
- Alertas internas por usuario, clasificadas por tipo

---

## 🔐 Sistema de Roles

El RBAC es **propio** (no usa el sistema de permisos nativo de Django) y totalmente gestionable desde la base de datos vía la interfaz de Roles — los roles no están hardcodeados en el código, salvo el trato especial que recibe el nombre `"Administrador"` (acceso total implícito).

### Roles creados por `init_roles` (semilla inicial, editable después)

| Rol | Descripción |
|-----|-------------|
| **Administrador** | Acceso total a todos los módulos |
| **Equipo SST** | Ver, crear, editar y consultar inspecciones/cronogramas |
| **Almacenista** | Inspecciones de almacenamiento e inventario |
| **Brigadista** | Inspecciones de extintores y botiquines |
| **Montacarguista** | Ver, crear y consultar inspecciones de montacargas |
| **Consulta** | Solo lectura (ver y consultar) |

### Permisos por Módulo
Cada módulo define sus propias acciones en `roles/models.py` (`PERMISSION_MATRIX`), con **48 permisos activos** en total repartidos en 11 módulos (usuarios, roles, cronograma, extintores, botiquines, procesos, almacenamiento, montacargas, activos, reportes, planos). Las acciones típicas son `view`, `create`, `edit`, `delete`, `details`; algunos módulos tienen acciones propias (`reset_password` en usuarios, `gestionar_movimientos` en activos).

---

## 🎨 Características

### ✅ Implementado
- Sistema de autenticación completo (login por email)
- 6 tipos de inspecciones + cronograma + reportes con exportación a Excel
- Gestión de activos físicos con trazabilidad de movimientos
- Ubicación de activos en planos SVG
- CRUD completo en todos los módulos
- Sistema de notificaciones (Toastr)
- **RBAC funcional y aplicado**: control de acceso en vistas vía `RolePermissionRequiredMixin`, template tags de permisos, simulación de roles
- Interfaz responsive
- Admin de Django configurado

### 📅 Futuro
- Exportación de inspecciones a PDF
- Notificaciones por email
- API REST
- Aplicación móvil

---

## 📁 Estructura del Proyecto

```
testOne/
├── core/              # Configuración Django (settings, urls)
├── users/             # Autenticación y gestión de usuarios
├── inspections/       # Cronograma, 5 módulos de inspección, áreas, reportes
├── roles/             # RBAC: roles, permisos, simulación de rol
├── gestion_activos/   # Inventario de activos físicos y trazabilidad
├── planos/            # Ubicación de activos sobre planos SVG
├── system_config/     # Configuración clave-valor del sistema
├── notifications/     # Notificaciones internas
├── templates/         # Plantillas HTML globales
├── static/            # CSS, JS, imágenes
└── manage.py          # CLI de Django
```

> Nota: `testOne` no es la raíz del repositorio git — el control de versiones vive en el directorio padre.

---

## 🛠️ Comandos Útiles

### Desarrollo
```bash
# Servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Shell interactivo
python manage.py shell
```

### RBAC
```bash
# Sincronizar permisos en BD con la matriz definida en roles/models.py
python manage.py init_permissions

# Inicializar/reinicializar roles base
python manage.py init_roles

# Ver roles en shell
python manage.py shell
>>> from roles.models import Role
>>> Role.objects.all()
```

### Base de Datos (PostgreSQL)
```bash
# Backup (dumpdata, recomendado sobre copiar archivos)
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > backup_YYYYMMDD.json

# Restaurar
python manage.py loaddata backup_YYYYMMDD.json
```

---

## 📚 Documentación

- **PROJECT_STATUS.md** - Estado general del proyecto
- **TECHNICAL_DOCS.md** - Documentación técnica detallada (arquitectura, modelos, flujo HTTP)
- **CLAUDE.md** - Guía de arquitectura para trabajar con Claude Code en este repo
- **NOTIFICATIONS_GUIDE.md** - Sistema de notificaciones

---

## 🔧 Tecnologías

### Backend
- Python 3.13
- Django 5.2.7
- PostgreSQL (activo) — SQLite solo como alternativa local comentada en `settings.py`

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5
- Font Awesome 6.4
- Toastr.js
- Google Fonts (Inter)

---

## 🤝 Contribuir

Este es un proyecto privado para Plastitec. Para cambios:

1. Crear rama feature
2. Hacer cambios
3. Commit con mensaje descriptivo
4. Push y crear Pull Request

---

## 📝 Notas Importantes

### Primer Uso
1. Ejecutar `python manage.py init_permissions` y `python manage.py init_roles` después de las migraciones
2. Crear un superusuario
3. Asignar rol "Administrador" al superusuario desde el admin

### Seguridad — pendiente antes de exponer el sistema fuera de un entorno controlado
El sistema está actualmente desplegado en una VM de pruebas internas. Antes de cualquier despliegue expuesto a usuarios externos o a internet:
- `SECRET_KEY` sigue siendo la generada por defecto por Django (`core/settings.py`) — rotarla y moverla a variable de entorno
- `DEBUG = True` y `ALLOWED_HOSTS = ['*']` están activos — con `DEBUG=True`, un error 500 muestra el stacktrace completo (incluye `SECRET_KEY` y credenciales de BD) a quien lo dispare
- Credenciales de PostgreSQL están hardcodeadas en `core/settings.py` — moverlas a variables de entorno
- Configurar HTTPS

### Backup
- La base de datos activa es PostgreSQL; usar `dumpdata`/`loaddata` o backups nativos de Postgres, no copiar `db.sqlite3` (archivo obsoleto, sin uso)
- Guardar archivos de migración en control de versiones

---

## 📞 Soporte

**Desarrollado por:** Antigravity AI  
**Cliente:** Plastitec  
**Última actualización:** 2026-10-23 (documentación revisada y sincronizada con el código real)

---

## 📄 Licencia

Propietario - Plastitec © 2026

---

## 🎯 Roadmap

### Estado actual
- ✅ Cronograma + 5 módulos de inspección + reportes con exportación a Excel
- ✅ Gestión de usuarios con autenticación por email
- ✅ Sistema de notificaciones (Toastr)
- ✅ RBAC completo: modelos, control de acceso en vistas, simulación de roles
- ✅ Gestión de activos físicos con trazabilidad de movimientos
- ✅ Ubicación de activos en planos SVG

### Próximo
- [ ] Exportación de inspecciones a PDF
- [ ] Notificaciones por email
- [ ] Endurecimiento de configuración para despliegue fuera de entorno de pruebas (`DEBUG`, `SECRET_KEY`, credenciales por variable de entorno)

### Futuro
- [ ] API REST
- [ ] Aplicación móvil
- [ ] Integración con sistemas externos

---

**¡Gracias por usar el Sistema de Gestión SST!** 🛡️
