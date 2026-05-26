from django import template

register = template.Library()


@register.simple_tag
def active(request, url):
    """Return 'active' when the current URL is under the given path
    segment.

    Match on full path segments split on '/' rather than substring `in`
    -- otherwise e.g. {% active request 'users' %} would mark itself
    active for any URL containing the word "users" anywhere, and the
    Growth nav item would light up on any path containing "growth".
    """
    if request.path == "/" and url == 'availability':
        return 'active'
    segments = request.path.strip('/').split('/')
    if url in segments:
        return 'active'
    return ''
