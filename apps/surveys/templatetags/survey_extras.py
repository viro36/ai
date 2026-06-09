from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу"""
    if dictionary is None:
        return ""
    return dictionary.get(key, "")


@register.filter
def get_range(value):
    """Создаёт список чисел от 1 до value"""
    return range(1, value + 1)
