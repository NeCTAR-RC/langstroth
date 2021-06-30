from django import template

register = template.Library()


@register.simple_tag
def active(request, url):
    if request.path == "/" and url == 'availability':
        return 'active'
    if url in request.path:
        return 'active'
    return ''
