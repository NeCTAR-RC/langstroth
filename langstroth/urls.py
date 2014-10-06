from django.conf.urls import handler500
from django.conf.urls import patterns, include, url

from langstroth import error

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',

    # Examples:
    url(r'^$', 'langstroth.views.index', name='home'),
    # url(r'^langstroth/', include('langstroth.foo.urls')),
    url(r'^growth/$', 'langstroth.views.growth', name='growth'),
    url(r'^domain/$', 'langstroth.views.domain', name='domain'),
    url(r'^domain/cores_per_domain$', 'langstroth.views.total_cores_per_domain', name='domain'),
    url(r'^growth/instance_count$', 'langstroth.views.total_instance_count'),
    url(r'^growth/used_cores$', 'langstroth.views.total_used_cores'),
    url(r'^allocations/', include('nectar_allocations.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

handler500 = error.handler500
