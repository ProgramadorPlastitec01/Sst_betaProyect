# 🚀 Guía Rápida: Fase 2 - Control de Acceso Funcional

## 📋 Resumen de Fase 1 (Completada)
✅ Modelos de Permission y Role creados  
✅ 36 permisos y 7 roles inicializados  
✅ CRUD completo del módulo Roles  
✅ Interfaz de asignación de permisos  
✅ Usuarios pueden tener rol asignado  

## 🎯 Objetivos de Fase 2

Hacer funcional el control de acceso implementando:
1. Middleware de validación de permisos
2. Decoradores para proteger vistas
3. Template tags para UI condicional
4. Aplicar protección a vistas existentes

---

## 1️⃣ MIDDLEWARE DE PERMISOS

### Crear: `roles/middleware.py`

```python
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class RBACMiddleware:
    """
    Middleware para validar permisos en cada request.
    """
    
    # URLs públicas que no requieren permisos
    PUBLIC_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
    ]
    
    # Mapeo de URLs a permisos requeridos
    URL_PERMISSIONS = {
        '/inspections/': ('inspections', 'view'),
        '/inspections/create/': ('inspections', 'create'),
        '/users/': ('users', 'view'),
        '/users/create/': ('users', 'create'),
        '/roles/': ('roles', 'view'),
        # ... agregar más según sea necesario
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar si el usuario está autenticado
        if request.user.is_authenticated:
            # Verificar si la URL requiere permisos
            if not self._is_public_url(request.path):
                required_perm = self._get_required_permission(request.path)
                if required_perm:
                    module, action = required_perm
                    if not request.user.has_perm_custom(module, action):
                        messages.error(request, 'No tienes permisos para acceder a esta página.')
                        return redirect('dashboard')
        
        response = self.get_response(request)
        return response
    
    def _is_public_url(self, path):
        return any(path.startswith(url) for url in self.PUBLIC_URLS)
    
    def _get_required_permission(self, path):
        for url_pattern, permission in self.URL_PERMISSIONS.items():
            if path.startswith(url_pattern):
                return permission
        return None
```

### Registrar en `core/settings.py`:

```python
MIDDLEWARE = [
    # ... otros middlewares
    'django.contrib.messages.middleware.MessageMiddleware',
    'roles.middleware.RBACMiddleware',  # ⬅️ AGREGAR AQUÍ
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

## 2️⃣ DECORADORES DE PERMISOS

### Crear: `roles/decorators.py`

```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def permission_required(module, action):
    """
    Decorador para proteger vistas basadas en funciones.
    
    Uso:
        @permission_required('users', 'create')
        def create_user(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.user.has_perm_custom(module, action):
                messages.error(request, f'No tienes permiso para {action} en {module}.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_required(role_name):
    """
    Decorador para requerir un rol específico.
    
    Uso:
        @role_required('Administrador')
        def admin_only_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.user.role or request.user.role.name != role_name:
                messages.error(request, f'Esta página requiere el rol: {role_name}.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### Mixin para Class-Based Views:

```python
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

class PermissionRequiredMixin(UserPassesTestMixin):
    """
    Mixin para proteger Class-Based Views.
    
    Uso:
        class UserCreateView(PermissionRequiredMixin, CreateView):
            permission_module = 'users'
            permission_action = 'create'
            ...
    """
    permission_module = None
    permission_action = None
    
    def test_func(self):
        if not self.permission_module or not self.permission_action:
            return True  # Si no se especifica, permitir acceso
        
        return self.request.user.has_perm_custom(
            self.permission_module, 
            self.permission_action
        )
    
    def handle_no_permission(self):
        messages.error(
            self.request, 
            f'No tienes permiso para {self.permission_action} en {self.permission_module}.'
        )
        return redirect('dashboard')
```

---

## 3️⃣ TEMPLATE TAGS

### Crear: `roles/templatetags/__init__.py`
```python
# Archivo vacío
```

### Crear: `roles/templatetags/permission_tags.py`

```python
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def has_perm(context, module, action):
    """
    Verifica si el usuario tiene un permiso.
    
    Uso en template:
        {% load permission_tags %}
        {% has_perm 'users' 'create' as can_create %}
        {% if can_create %}
            <a href="...">Crear Usuario</a>
        {% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    return request.user.has_perm_custom(module, action)


@register.filter
def can_view(user, module):
    """
    Filtro para verificar permiso de visualización.
    
    Uso:
        {% if user|can_view:'users' %}
            ...
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    return user.has_perm_custom(module, 'view')


@register.filter
def can_create(user, module):
    """Verifica permiso de creación"""
    if not user.is_authenticated:
        return False
    return user.has_perm_custom(module, 'create')


@register.filter
def can_edit(user, module):
    """Verifica permiso de edición"""
    if not user.is_authenticated:
        return False
    return user.has_perm_custom(module, 'edit')


@register.filter
def can_delete(user, module):
    """Verifica permiso de eliminación"""
    if not user.is_authenticated:
        return False
    return user.has_perm_custom(module, 'delete')
```

---

## 4️⃣ APLICAR A VISTAS EXISTENTES

### Ejemplo: Proteger vistas de usuarios

**En `users/views.py`:**

```python
from roles.decorators import permission_required
from roles.mixins import PermissionRequiredMixin

# Function-Based View
@permission_required('users', 'create')
def create_user(request):
    ...

# Class-Based View
class UserCreateView(PermissionRequiredMixin, CreateView):
    permission_module = 'users'
    permission_action = 'create'
    model = CustomUser
    ...

class UserUpdateView(PermissionRequiredMixin, UpdateView):
    permission_module = 'users'
    permission_action = 'edit'
    ...

class UserDeleteView(PermissionRequiredMixin, DeleteView):
    permission_module = 'users'
    permission_action = 'delete'
    ...
```

---

## 5️⃣ ACTUALIZAR TEMPLATES

### Ejemplo: Ocultar botones según permisos

**En `templates/users/user_list.html`:**

```html
{% load permission_tags %}

<div class="actions">
    {% has_perm 'users' 'create' as can_create_user %}
    {% if can_create_user %}
        <a href="{% url 'user_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Crear Usuario
        </a>
    {% endif %}
</div>

<table>
    {% for user in users %}
    <tr>
        <td>{{ user.email }}</td>
        <td>
            {% has_perm 'users' 'edit' as can_edit_user %}
            {% has_perm 'users' 'delete' as can_delete_user %}
            
            {% if can_edit_user %}
                <a href="{% url 'user_edit' user.pk %}">Editar</a>
            {% endif %}
            
            {% if can_delete_user %}
                <a href="{% url 'user_delete' user.pk %}">Eliminar</a>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</table>
```

### Actualizar Sidebar en `base.html`:

```html
{% load permission_tags %}

<ul class="sidebar-menu">
    <li>
        <a href="{% url 'dashboard' %}">
            <i class="fas fa-th-large"></i> Dashboard
        </a>
    </li>
    
    {% if user|can_view:'schedule' %}
    <li>
        <a href="{% url 'inspection_list' %}">
            <i class="fas fa-calendar-alt"></i> Cronograma
        </a>
    </li>
    {% endif %}
    
    {% if user|can_view:'extinguisher' %}
    <li>
        <a href="{% url 'extinguisher_list' %}">
            <i class="fas fa-fire-extinguisher"></i> Extintores
        </a>
    </li>
    {% endif %}
    
    {% if user|can_view:'users' %}
    <li>
        <a href="{% url 'user_list' %}">
            <i class="fas fa-users"></i> Usuarios
        </a>
    </li>
    {% endif %}
    
    {% if user|can_view:'roles' %}
    <li>
        <a href="{% url 'role_list' %}">
            <i class="fas fa-user-shield"></i> Roles
        </a>
    </li>
    {% endif %}
</ul>
```

---

## 6️⃣ CREAR PÁGINA DE "SIN PERMISOS"

### Crear: `templates/errors/no_permission.html`

```html
{% extends 'base.html' %}

{% block title %}Acceso Denegado{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center mt-5">
        <div class="col-md-6 text-center">
            <i class="fas fa-lock fa-5x text-danger mb-4"></i>
            <h1>Acceso Denegado</h1>
            <p class="lead">No tienes permisos para acceder a esta página.</p>
            <p>Si crees que esto es un error, contacta al administrador del sistema.</p>
            <a href="{% url 'dashboard' %}" class="btn btn-primary mt-3">
                <i class="fas fa-home"></i> Volver al Dashboard
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 7️⃣ TESTING

### Crear: `roles/tests.py`

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from roles.models import Role, Permission

User = get_user_model()

class PermissionTestCase(TestCase):
    def setUp(self):
        # Crear permisos
        self.perm_view = Permission.objects.create(
            module='users',
            action='view',
            codename='users_view'
        )
        self.perm_create = Permission.objects.create(
            module='users',
            action='create',
            codename='users_create'
        )
        
        # Crear rol
        self.role = Role.objects.create(name='Test Role')
        self.role.permissions.add(self.perm_view)
        
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.user.role = self.role
        self.user.save()
    
    def test_user_has_permission(self):
        """Usuario debe tener permiso de visualización"""
        self.assertTrue(self.user.has_perm_custom('users', 'view'))
    
    def test_user_lacks_permission(self):
        """Usuario no debe tener permiso de creación"""
        self.assertFalse(self.user.has_perm_custom('users', 'create'))
    
    def test_user_without_role(self):
        """Usuario sin rol no debe tener permisos"""
        user_no_role = User.objects.create_user(
            username='norole',
            email='norole@test.com',
            password='testpass123'
        )
        self.assertFalse(user_no_role.has_perm_custom('users', 'view'))
```

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### Fase 2.1: Infraestructura
- [ ] Crear `roles/middleware.py`
- [ ] Crear `roles/decorators.py`
- [ ] Crear `roles/mixins.py`
- [ ] Crear `roles/templatetags/permission_tags.py`
- [ ] Registrar middleware en settings
- [ ] Crear página de error "Sin permisos"

### Fase 2.2: Aplicar a Módulos Existentes
- [ ] Proteger vistas de Usuarios
- [ ] Proteger vistas de Inspecciones
- [ ] Proteger vistas de Cronograma
- [ ] Proteger vistas de Extintores
- [ ] Proteger vistas de Botiquines
- [ ] Proteger vistas de Procesos
- [ ] Proteger vistas de Almacenamiento
- [ ] Proteger vistas de Montacargas
- [ ] Proteger vistas de Roles

### Fase 2.3: Actualizar UI
- [ ] Actualizar sidebar con template tags
- [ ] Actualizar botones de acción en listados
- [ ] Ocultar opciones según permisos
- [ ] Mostrar rol del usuario en navbar

### Fase 2.4: Testing
- [ ] Tests unitarios de permisos
- [ ] Tests de decoradores
- [ ] Tests de middleware
- [ ] Tests de template tags
- [ ] Tests de integración

---

## 🎯 ORDEN RECOMENDADO DE IMPLEMENTACIÓN

1. **Crear infraestructura** (middleware, decorators, template tags)
2. **Probar con un módulo** (ej: Usuarios)
3. **Validar funcionamiento**
4. **Aplicar al resto de módulos**
5. **Actualizar UI**
6. **Testing completo**

---

## 💡 CONSEJOS

- Implementa módulo por módulo, no todo a la vez
- Prueba cada cambio antes de continuar
- Mantén un usuario Administrador para testing
- Documenta cualquier cambio en la lógica de permisos
- Considera crear roles de prueba para testing

---

**¿Listo para comenzar la Fase 2?** 🚀
