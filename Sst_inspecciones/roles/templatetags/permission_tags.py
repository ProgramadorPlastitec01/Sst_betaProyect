from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def has_permission(context, module, action):
    """
    Template tag para verificar permisos de rol en templates.
    Uso: {% has_permission 'users' 'view' as can_view_users %}
    o directamente en if: {% if has_permission 'users' 'view' %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
        
    # Verificar si el usuario tiene el método custom (depende del modelo CustomUser)
    if hasattr(request.user, 'has_perm_custom'):
        return request.user.has_perm_custom(module, action)
        
    return False


@register.filter
def dict_value(d, key):
    """
    Filtro para acceder a un diccionario por clave dinámica en templates.
    Uso: {{ my_dict|dict_value:dynamic_key }}
    """
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def module_icon(module_code):
    """
    Retorna la clase de icono Font Awesome para un código de módulo.
    Uso: {{ row.module_code|module_icon }}
    """
    icons = {
        'users':        'fa-users',
        'roles':        'fa-user-shield',
        'schedule':     'fa-calendar-alt',
        'extinguisher': 'fa-fire-extinguisher',
        'first_aid':    'fa-first-aid',
        'process':      'fa-industry',
        'storage':      'fa-warehouse',
        'forklift':     'fa-truck-loading',
        'assets':       'fa-boxes',
        'reports':      'fa-chart-bar',
        'planos':       'fa-map',
    }
    return icons.get(module_code, 'fa-layer-group')
