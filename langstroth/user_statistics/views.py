from json import dumps

from django.http import HttpResponse
from django.shortcuts import render

from langstroth.user_statistics.services.user_statistics \
    import find_daily_accumulated_users


# Web pages
def user_registrations_page(request):
    context = {
        "title": "User Registrations",
        "tagline": "Since December 2011."}
    return render(request, "user_statistics.html", context)


# Web services with JSON pay loads.
def registrations_frequency(request):
    q_from = request.GET.get('from')
    q_until = request.GET.get('until')

    registration_cumulative_history = \
        find_daily_accumulated_users(q_from, q_until)
    json_string = dumps(registration_cumulative_history)
    return HttpResponse(json_string, "application/json")
