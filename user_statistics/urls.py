from django.conf.urls import patterns, url
from user_statistics import views


urlpatterns = patterns(
    '',

    url(r'^$',
        views.user_registrations_page, name='user_registrations'),
    url(r'^rest/registrations/frequency$',
        views.registrations_frequency, name='registrations_frequency'),
)
