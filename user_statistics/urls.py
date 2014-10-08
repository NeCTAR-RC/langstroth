from django.conf.urls import patterns, url
from user_statistics import views


urlpatterns = patterns(
    '',

    # Web pages

    url(r'^$', views.index_page,
        name='index_page'),

    url(r'^registrations/visualisation$',
        views.trend_visualisation_page, name='trend_visualisation'),

    # Web services with JSON pay loads.

    url(r'^rest/registrations/frequency$',
        views.registrations_frequency, name='registrations_frequency'),
)
