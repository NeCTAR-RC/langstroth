from django.urls import re_path
from langstroth.nectar_allocations import views

urlpatterns = [
    re_path(r'^$', views.index_page, name='index_page'),
    re_path(r'^applications/(?P<allocation_request_id>[0-9]+)/approved$',
            views.project_details_page, name='project_details_page'),

]
