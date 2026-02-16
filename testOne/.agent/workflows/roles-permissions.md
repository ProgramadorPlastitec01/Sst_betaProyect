---
description: Gestión de Roles y Permisos (R-RH-SST-Permissions)
---

# Gestión de Roles y Permisos

Este módulo gestiona el acceso a las diferentes funcionalidades del sistema mediante Roles y Permisos granulares.

## Características Principales

1.  **Roles**: Grupos de usuarios con un conjunto definido de permisos (ej. Inspector, Supervisor, Administrador).
2.  **Permisos Granulares**: Control de acceso por módulo (Extintores, Botiquines, etc.) y acción (Ver, Crear, Editar, Eliminar).
3.  **Validación Multinivel**:
    *   **Menú Lateral**: Se ocultan los módulos no permitidos dinámicamente.
    *   **Protección de Rutas**: Middleware/Mixin que impide acceso directo por URL.
    *   **Vistas de Acción**: Botones y formularios protegidos según permisos de edición/creación.
4.  **Rol Administrador**: Acceso total automático sin necesidad de configuración manual de permisos.

## Estructura del Código

*   **`roles/models.py`**: Define `Role` y `Permission`.
*   **`users/models.py`**: Extiende `CustomUser` con método `has_perm_custom` y lógica de Superusuario/Admin.
*   **`roles/mixins.py`**: `RolePermissionRequiredMixin` para proteger ViewClasses.
*   **`roles/templatetags/permission_tags.py`**: Tag `{% has_permission %}` para uso en templates (sidebar).
*   **`inspections/views.py`**: Todas las vistas de inspección están protegidas con el Mixin.

## Uso

### Crear un Rol
1.  Ir a Configuración -> Roles.
2.  Crear Nuevo Rol.
3.  Asignar Permisos desde la matriz de configuración en detalle del rol.

### Asignar Rol a Usuario
1.  Ir a Usuarios -> Editar Usuario.
2.  Seleccionar el Rol deseado.

## Notas Técnicas
- El rol con nombre exacto "Administrador" tiene bypass de seguridad (siempre retorna True).
- Los permisos se cargan dinámicamente basados en `MODULE_CHOICES` del modelo `Permission`.
