import json
from django import template

register = template.Library()

@register.filter
def json_loads(value):
    """Преобразует JSON строку в список Python"""
    if not value:
        return []
    try:
        # Пробуем распарсить JSON
        result = json.loads(value)
        # Если результат не список, делаем из него список
        if isinstance(result, list):
            return result
        else:
            return [result]
    except (json.JSONDecodeError, TypeError):
        # Если это не JSON, возвращаем как есть в списке
        return [value] if value else []