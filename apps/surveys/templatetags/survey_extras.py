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


@register.filter
def in_group(user, group_name):
    """Проверяет, состоит ли пользователь в группе"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()
