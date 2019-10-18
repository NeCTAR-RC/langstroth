from django.conf.urls import url
from user_statistics import views


urlpatterns = [
    url(r'^$',
        views.user_registrations_page, name='user_registrations'),
    url(r'^rest/registrations/frequency$',
        views.registrations_frequency, name='registrations_frequency'),
]
