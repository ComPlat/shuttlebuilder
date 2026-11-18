from django import template

from main_app.models import GitInstance

register = template.Library()


@register.simple_tag
def active_shuttle_version():
    """Shuttle version of the active git instance ('' if none is active or the version is unknown)."""
    return GitInstance.objects.filter(is_active=True).values_list('shuttle_version', flat=True).first() or ''
