from django.urls import re_path
from user_statistics import views


urlpatterns = [
    re_path(r'^$',
            views.user_registrations_page, name='user_registrations'),
    re_path(r'^rest/registrations/frequency$',
            views.registrations_frequency, name='registrations_frequency'),
]
