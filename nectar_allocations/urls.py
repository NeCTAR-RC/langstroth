from django.conf.urls import patterns, url
from nectar_allocations import views

urlpatterns = patterns('',
    # Web pages
    url(r'^$', views.index_page, name='index_page'),
    url(r'^applications/approved/visualisation$', views.allocation_visualisation_page, name='visualisation'),
    url(r'^applications/(?P<allocation_request_id>[0-9]+)/approved$', views.project_details_page, name='project_details_page'),
    url(r'^applications/(?P<allocation_request_id>[0-9]+)/history$', views.project_allocations_page, name='project_allocations_page'),

    # Web services with JSON pay loads.
    url(r'^rest/for_codes$', views.for_codes, name='for_codes'),
    url(r'^rest/applications/approved/tree$', views.allocation_tree, name='allocation_tree'),
    url(r'^rest/applications/(?P<allocation_request_id>[0-9]+)/history$', views.project_allocations, name='project_allocations'),
    url(r'^rest/applications/(?P<allocation_request_id>[0-9]+)/approved$', views.project_summary, name='project_summary'),
)
