# 🛡️ Sistema de Gestión SST - Plastitec

Sistema integral de Seguridad y Salud en el Trabajo (SST) con control de acceso basado en roles (RBAC).

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.13+
- Django 5.2.7
- SQLite (incluido)

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

# 5. Inicializar roles y permisos
python manage.py init_roles

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
- Login/Logout
- Gestión de usuarios
- Asignación de roles

### 2. Inspecciones
- **Cronograma Anual** - Planificación de inspecciones
- **Extintores** - Control de extintores
- **Botiquines** - Inspección de primeros auxilios
- **Procesos** - Inspección de instalaciones
- **Almacenamiento** - Control de almacenes
- **Montacargas** - Inspección de equipos

### 3. Roles y Permisos (RBAC)
- Gestión de roles
- Asignación de permisos
- Control de acceso granular

---

## 🔐 Sistema de Roles

### Roles Predefinidos

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **Administrador** | Acceso total | Todos (36) |
| **SST** | Coordinador SST | 21 permisos |
| **COPASST** | Comité SST | Solo visualización |
| **Consulta** | Auditor | Solo visualización |
| **Brigadista** | Brigada emergencias | Extintores, Botiquines |
| **Montacarguista** | Operador | Montacargas |
| **Almacenista** | Personal almacén | Almacenamiento |

### Permisos por Módulo
Cada módulo tiene 4 niveles de permiso:
- **Ver** - Visualizar información
- **Crear** - Registrar nuevos elementos
- **Editar** - Modificar existentes
- **Eliminar** - Borrar registros

---

## 🎨 Características

### ✅ Implementado
- Sistema de autenticación completo
- 6 tipos de inspecciones
- CRUD completo en todos los módulos
- Sistema de notificaciones (Toastr)
- Gestión de roles y permisos
- Interfaz responsive
- Admin de Django configurado

### ⏳ En Desarrollo (Fase 2)
- Middleware de control de acceso
- Decoradores de permisos
- Template tags de permisos
- UI condicional según permisos

### 📅 Futuro
- Exportación a PDF
- Dashboard con gráficos
- Notificaciones por email
- API REST
- Aplicación móvil

---

## 📁 Estructura del Proyecto

```
testOne/
├── core/              # Configuración Django
├── users/             # Módulo de usuarios
├── inspections/       # Módulo de inspecciones
├── roles/             # Módulo RBAC
├── templates/         # Plantillas HTML
├── static/            # CSS, JS, imágenes
├── db.sqlite3         # Base de datos
└── manage.py          # CLI de Django
```

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
# Inicializar/reinicializar roles y permisos
python manage.py init_roles

# Ver roles en shell
python manage.py shell
>>> from roles.models import Role
>>> Role.objects.all()
```

### Base de Datos
```bash
# Backup
copy db.sqlite3 db_backup.sqlite3

# Restaurar
copy db_backup.sqlite3 db.sqlite3
```

---

## 📚 Documentación

- **PROJECT_STATUS.md** - Estado general del proyecto
- **RBAC_IMPLEMENTATION_CHECKPOINT.md** - Checkpoint Fase 1 RBAC
- **RBAC_PHASE2_GUIDE.md** - Guía para implementar Fase 2
- **NOTIFICATIONS_GUIDE.md** - Sistema de notificaciones

---

## 🔧 Tecnologías

### Backend
- Python 3.13
- Django 5.2.7
- SQLite

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
1. Ejecutar `python manage.py init_roles` después de las migraciones
2. Crear un superusuario
3. Asignar rol "Administrador" al superusuario desde el admin

### Seguridad
- Cambiar `SECRET_KEY` en producción
- Configurar `DEBUG = False` en producción
- Usar base de datos PostgreSQL/MySQL en producción
- Configurar HTTPS

### Backup
- Hacer backup de `db.sqlite3` regularmente
- Guardar archivos de migración en control de versiones

---

## 📞 Soporte

**Desarrollado por:** Antigravity AI  
**Cliente:** Plastitec  
**Versión:** 1.0.0-RBAC-Phase1  
**Última actualización:** 2026-02-12  

---

## 📄 Licencia

Propietario - Plastitec © 2026

---

## 🎯 Roadmap

### Versión 1.0 (Actual)
- ✅ Sistema base de inspecciones
- ✅ Gestión de usuarios
- ✅ Sistema de notificaciones
- ✅ RBAC Fase 1

### Versión 1.1 (Próxima)
- [ ] RBAC Fase 2 - Control de acceso funcional
- [ ] Middleware de permisos
- [ ] UI condicional

### Versión 1.2
- [ ] Exportación a PDF
- [ ] Dashboard con estadísticas
- [ ] Reportes personalizados

### Versión 2.0
- [ ] API REST
- [ ] Notificaciones por email
- [ ] Aplicación móvil
- [ ] Integración con sistemas externos

---

**¡Gracias por usar el Sistema de Gestión SST!** 🛡️
