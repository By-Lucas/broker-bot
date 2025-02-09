from django import template

register = template.Library()

@register.filter
def replace_comma(value):
    """Substitui vírgulas por pontos para compatibilidade com campos numéricos."""
    if isinstance(value, str):
        return value.replace(",", ".")
    return str(value).replace(",", ".")
