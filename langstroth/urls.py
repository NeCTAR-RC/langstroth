from django.conf.urls import patterns, include, url

from langstroth import error

urlpatterns = patterns(
    '',

    url(r'^$', 'langstroth.views.index', name='home'),

    # Domain Visualisations
    url(r'^domain/$', 'langstroth.views.domain', name='domain'),
    url(r'^domain/cores_per_domain$',
        'langstroth.views.total_cores_per_domain', name='domain'),

    # Growth Visualisations
    url(r'^growth/infrastructure/$', 'langstroth.views.growth', name='growth'),
    url(r'^growth/users/', include('user_statistics.urls')),
    url(r'^growth/instance_count$', 'langstroth.views.total_instance_count'),
    url(r'^growth/used_cores$', 'langstroth.views.total_used_cores'),

    # Allocations Browser
    url(r'^allocations/', include('nectar_allocations.urls')),
)

handler500 = error.handler500
handler400 = error.handler500
