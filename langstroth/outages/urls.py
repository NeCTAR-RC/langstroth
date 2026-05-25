from django.urls import re_path

from langstroth.outages import views

app_name = 'outages'
urlpatterns = [
    re_path(r'^$', views.index_page, name='list'),
    re_path(
        r'^(?P<pk>\d+)/$', views.OutageDetailView.as_view(), name='detail'
    ),
    re_path(r'^create/$', views.OutageCreateView.as_view(), name='create'),
    re_path(
        r'^(?P<pk>\d+)/add_update/$',
        views.UpdateOutageView.as_view(),
        name='add_update',
    ),
    re_path(r'^(?P<pk>\d+)/end/$', views.EndOutageView.as_view(), name='end'),
    re_path(
        r'^(?P<pk>\d+)/cancel/$',
        views.CancelOutageView.as_view(),
        name='cancel',
    ),
]
