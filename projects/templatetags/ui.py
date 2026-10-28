from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, ru, uz):
    return uz if context.get('uz') else ru


@register.simple_tag
def icon(name, extra=''):
    return format_html('<svg class="icon {}" aria-hidden="true"><use href="#i-{}"></use></svg>', extra, name)
