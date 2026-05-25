from json import dumps
import re

from django.http import HttpResponse
from django.shortcuts import render

from langstroth.user_statistics.services.user_statistics import (
    find_daily_accumulated_users,
)


# Graphite time-window patterns: yyyymmdd or a relative offset like "-6months".
# Anything else is dropped (the service falls back to its configured default).
_RELATIVE_RE = re.compile(
    r'^-?\d+(?:s|seconds?|min|minutes?|h|hours?|d|days?|w|weeks?|mon|months?|y|years?)$'
)
_ABSOLUTE_RE = re.compile(r'^\d{8}$')


def _safe_window(value):
    if value is None:
        return None
    if _RELATIVE_RE.match(value) or _ABSOLUTE_RE.match(value):
        return value
    return None


# Web pages
def user_registrations_page(request):
    context = {
        "title": "User Registrations",
        "tagline": "Since December 2011.",
    }
    return render(request, "user_statistics.html", context)


# Web services with JSON pay loads.
def registrations_frequency(request):
    q_from = _safe_window(request.GET.get('from'))
    q_until = _safe_window(request.GET.get('until'))

    registration_cumulative_history = find_daily_accumulated_users(
        q_from, q_until
    )
    json_string = dumps(registration_cumulative_history)
    return HttpResponse(json_string, "application/json")
