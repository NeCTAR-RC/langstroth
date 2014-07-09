from django.conf.urls import patterns, url
from nectar_allocations import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^visualisation$', views.allocation_visualisation, name='visualisation'),
    url(r'^for_codes$', views.for_codes, name='for_codes'),
    url(r'^allocation_tree$', views.allocation_tree, name='allocation_tree'),
    url(r'^(?P<allocation_request_id>[0-9]+)/project$', views.project_details, name='project_details'),
    url(r'^(?P<allocation_request_id>[0-9]+)/project_summary$', views.project_summary, name='project_summary'),
)
