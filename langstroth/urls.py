from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView

from langstroth import error
from langstroth import views


urlpatterns = [

    url(r'^$', views.index, name='home'),

    # Composition Visualisations
    url(r'^composition/(?P<name>\w+)/$', views.composition,
        name='composition'),
    url(r'^composition/(?P<name>\w+)/cores$', views.composition_cores,
        name='composition'),

    # Redirect from old url
    url(r'^domain/$', RedirectView.as_view(
        url='/composition/domain', permanent=True),
        name='composition'),

    # Usage Visualisations
    url(r'^growth/infrastructure/$', views.growth, name='growth'),
    url(r'^growth/users/', include('user_statistics.urls')),
    url(r'^growth/instance_count$', views.total_instance_count),
    url(r'^growth/used_cores$', views.total_used_cores),

    # Allocations Browser
    url(r'^allocations/', include('nectar_allocations.urls')),
]

handler500 = error.handler500
handler400 = error.handler400
