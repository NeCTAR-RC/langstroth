from django.conf.urls import patterns, url
from nectar_allocations import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^visualisation$', views.allocation_visualisation, name='visualisation'),
    url(r'^for_codes$', views.for_codes, name='for_codes'),
    url(r'^allocation_tree$', views.allocation_tree, name='allocation_tree'),
)
