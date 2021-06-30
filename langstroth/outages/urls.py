from django.urls import re_path
from langstroth.outages import views

urlpatterns = [
    re_path(r'^$', views.index_page, name='outage_list'),
    re_path(r'^(?P<pk>\d+)$', views.OutageDetailView.as_view(),
            name='outage_view'),
]
