from json import dumps
from django.http import HttpResponse
from django.shortcuts import render
from user_statistics.services.user_statistics \
    import find_daily_accumulated_users


# Web pages


def index_page(request):
    return trend_visualisation_page(request)


def trend_visualisation_page(request):
    context = {
        "title": "User Registrations",
        "tagline": ""}
    return render(request, "user_statistics.html", context)


# Web services with JSON pay loads.


def registrations_frequency(request):
    registration_cumulative_history = \
        find_daily_accumulated_users()
    json_string = dumps(registration_cumulative_history)
    return HttpResponse(json_string, "application/json")
