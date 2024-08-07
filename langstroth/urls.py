from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import re_path
from django.views.generic.base import RedirectView
from mozilla_django_oidc import views as oidc_views
from rest_framework import routers

from langstroth import error
from langstroth.outages import api
from langstroth import views


router = routers.DefaultRouter()
router.register(r'outages', api.OutageViewSet, basename='outage')


urlpatterns = [

    re_path(r'^$', views.index, name='home'),

    # Composition Visualisations
    re_path(r'^composition/(?P<name>\w+)/$', views.composition,
            name='composition'),
    re_path(r'^composition/(?P<name>\w+)/cores$', views.composition_cores,
            name='composition'),

    # Redirect from old url
    re_path(r'^domain/$',
            RedirectView.as_view(url='/composition/domain', permanent=True),
            name='composition'),

    # Usage Visualisations
    re_path(r'^growth/infrastructure/$', views.growth, name='growth'),
    re_path(r'^growth/users/', include('langstroth.user_statistics.urls')),
    re_path(r'^growth/instance_count$', views.total_instance_count),
    re_path(r'^growth/used_cores$', views.total_used_cores),

    # Allocations Browser
    re_path(r'^allocations/', include('langstroth.nectar_allocations.urls')),

    # Outages
    re_path(r'^outages/', include('langstroth.outages.urls')),

    # API
    re_path(r'^api/v1/', include(router.urls)),

    # Favicon (dev)
    re_path(r'^favicon\.ico$',
            RedirectView.as_view(url='/static/img/favicon.ico')),

    # Timezone detection
    path('tz_detect/', include('tz_detect.urls')),

    # Health checks
    path('healthcheck/', include('health_check.urls')),
]

if settings.USE_OIDC:
    urlpatterns += [
        # Admin Interface
        path('admin/login/',
             oidc_views.OIDCAuthenticationRequestView.as_view(), name='login'),
        path('admin/', admin.site.urls),

        # OIDC auth
        path('oidc/', include('mozilla_django_oidc.urls')),
        path('login/',
             oidc_views.OIDCAuthenticationRequestView.as_view(), name='login'),
    ]
else:
    urlpatterns += [
        # Admin Interface
        path('admin/', admin.site.urls),
        path("login/",
             auth_views.LoginView.as_view(template_name='admin/login.html'),
             name='login'),
    ]

handler500 = error.handler500
handler400 = error.handler400
