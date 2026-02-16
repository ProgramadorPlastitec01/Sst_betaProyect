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
