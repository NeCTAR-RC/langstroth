from django.conf.urls import patterns, include, url

from langstroth import error


urlpatterns = patterns(
    '',

    url(r'^$', 'langstroth.views.index', name='home'),

    # Domain Visualisations
    url(r'^domain/$', 'langstroth.views.domain', name='domain'),
    url(r'^domain/cores_per_domain$',
        'langstroth.views.total_cores_per_domain', name='domain'),

    # Usage Visualisations
    url(r'^growth/infrastructure/$', 'langstroth.views.growth', name='growth'),
    url(r'^faults/$', 'langstroth.views.faults', name='faults'),
    url(r'^faults/instance_faults$', 'langstroth.views.total_faults'),
    url(r'^growth/users/', include('user_statistics.urls')),
    url(r'^growth/instance_count$', 'langstroth.views.total_instance_count'),
    url(r'^growth/used_cores$', 'langstroth.views.total_used_cores'),
    url(r'^capacity/(?P<ram_size>[0-9]+)$', 'langstroth.views.total_capacity'),
    url(r'^capacity/$', 'langstroth.views.capacity', name='capacity'),

    # Allocations Browser
    url(r'^allocations/', include('nectar_allocations.urls')),

)

handler500 = error.handler500
handler400 = error.handler500
