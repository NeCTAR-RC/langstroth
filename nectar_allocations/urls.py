from django.conf.urls import patterns, url
from nectar_allocations import views

urlpatterns = patterns(
    '',

    url(r'^$', views.index_page, name='index_page'),
    url(r'^applications/(?P<allocation_request_id>[0-9]+)/approved$',
        views.project_details_page, name='project_details_page'),

)
