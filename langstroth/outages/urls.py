from django.urls import re_path
from langstroth.outages import views

urlpatterns = [
    re_path(r'^$', views.index_page,
            name='outage_list'),
    re_path(r'^(?P<pk>\d+)$', views.OutageDetailView.as_view(),
            name='outage'),
    re_path(r'^scheduled/$', views.CreateScheduledView.as_view(),
            name='create_scheduled'),
    re_path(r'^unscheduled/$', views.CreateUnscheduledView.as_view(),
            name='create_unscheduled'),
    re_path(r'^(?P<pk>\d+)/add_update/$', views.UpdateOutageView.as_view(),
            name='add_update'),
    re_path(r'^(?P<pk>\d+)/start/$', views.StartOutageView.as_view(),
            name='start'),
    re_path(r'^(?P<pk>\d+)/end/$', views.EndOutageView.as_view(),
            name='end'),
    re_path(r'^(?P<pk>\d+)/cancel/$', views.CancelOutageView.as_view(),
            name='cancel'),
]
