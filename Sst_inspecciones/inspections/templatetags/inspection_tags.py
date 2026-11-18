from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.filter
def content_type_id(obj):
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj).id

@register.simple_tag
def get_content_type_for_model(model_name):
    # This might need improvement to map strings to models
    pass
