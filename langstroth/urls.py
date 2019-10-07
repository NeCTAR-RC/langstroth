from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from langstroth import error


urlpatterns = patterns(
    '',

    url(r'^$', 'langstroth.views.index', name='home'),

    # Composition Visualisations
    url(r'^composition/(?P<name>\w+)/$', 'langstroth.views.composition',
        name='composition'),
    url(r'^composition/(?P<name>\w+)/cores$',
        'langstroth.views.composition_cores', name='composition'),

    # Redirect from old url
    url(r'^domain/$', RedirectView.as_view(
        url='/composition/domain', permanent=True),
        name='composition'),

    # Usage Visualisations
    url(r'^growth/infrastructure/$', 'langstroth.views.growth', name='growth'),
    url(r'^faults/$', 'langstroth.views.faults', name='faults'),
    url(r'^faults/instance_faults$', 'langstroth.views.total_faults'),
    url(r'^growth/users/', include('user_statistics.urls')),
    url(r'^growth/instance_count$', 'langstroth.views.total_instance_count'),
    url(r'^growth/used_cores$', 'langstroth.views.total_used_cores'),

    # Allocations Browser
    url(r'^allocations/', include('nectar_allocations.urls')),

)

handler500 = error.handler500
handler400 = error.handler500
