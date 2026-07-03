from django import template

register = template.Library()


@register.filter
def get_field(form, field_name):
    """Получает поле формы по имени"""
    try:
        return form[field_name]
    except KeyError:
        return None
