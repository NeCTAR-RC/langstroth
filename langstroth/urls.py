from django.conf.urls import include
from django.urls import re_path
from django.views.generic.base import RedirectView

from langstroth import error
from langstroth import views


urlpatterns = [

    re_path(r'^$', views.index, name='home'),

    # Composition Visualisations
    re_path(r'^composition/(?P<name>\w+)/$', views.composition,
            name='composition'),
    re_path(r'^composition/(?P<name>\w+)/cores$', views.composition_cores,
            name='composition'),

    # Redirect from old url
    re_path(r'^domain/$',
            RedirectView.as_view(url='/composition/domain', permanent=True),
            name='composition'),

    # Usage Visualisations
    re_path(r'^growth/infrastructure/$', views.growth, name='growth'),
    re_path(r'^growth/users/', include('user_statistics.urls')),
    re_path(r'^growth/instance_count$', views.total_instance_count),
    re_path(r'^growth/used_cores$', views.total_used_cores),

    # Allocations Browser
    re_path(r'^allocations/', include('nectar_allocations.urls')),
]

handler500 = error.handler500
handler400 = error.handler400
