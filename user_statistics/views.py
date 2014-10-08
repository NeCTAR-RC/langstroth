from json import dumps
from django.http import HttpResponse
from django.shortcuts import render
from user_statistics.services.user_statistics import UserStatistics


# Web pages


def index_page(request):
    return trend_visualisation_page(request)


def trend_visualisation_page(request):
    context = {
        "title": "User Registrations",
        "tagline": ""}
    return render(request, "user_statistics.html", context)


# Web services with JSON pay loads.


def end_month_str(date):
    return UserStatistics.last_date_of_month(date).strftime('%Y-%m-%d')


def registrations_frequency(request):
    registration_frequency = UserStatistics.monthly_frequency()
    # Convert all dates to string dates.
    registrations = [
        {
            'date': end_month_str(item['date']),
            'count': item['count']
        } for item in registration_frequency
    ]
    json_string = dumps(registrations)
    return HttpResponse(json_string, "application/json")
