"""Filtros auxiliares para templates."""
from __future__ import annotations

from django import template

register = template.Library()


@register.filter(name="dictitem")
def dictitem(value, key):
    """Acessa ``value[key]`` em dicts dentro de templates.

    Permite chamar ``{{ mydict|dictitem:mykey }}`` — algo que o Django
    não suporta nativamente quando a chave é uma variável do contexto.
    """
    if value is None:
        return ""
    try:
        return value[key]
    except (KeyError, TypeError, IndexError):
        try:
            return value[str(key)]
        except (KeyError, TypeError):
            return ""
