from django_filters import rest_framework as rest_filters
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions
from rest_framework import serializers
from rest_framework import viewsets

from langstroth.outages import filters
from langstroth.outages import models


class OutagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class OutageUpdateSerializer(serializers.ModelSerializer):
    # Backwards-compat: severity moved off OutageUpdate onto Outage in the
    # workflow-unification refactor. Expose the parent outage's severity
    # under the old name so existing clients (python-langstrothclient)
    # keep working.
    severity = serializers.IntegerField(
        source='outage.severity', read_only=True
    )

    class Meta:
        model = models.OutageUpdate
        fields = ('content', 'time', 'status', 'severity')


class OutageSerializer(serializers.ModelSerializer):
    severity_display = serializers.ReadOnlyField()
    scheduled_display = serializers.ReadOnlyField()
    status_display = serializers.ReadOnlyField()
    # Backwards-compat aliases for the pre-refactor field names. The
    # underlying fields (`start`, `planned_end`, `severity`) are also
    # exposed; these aliases exist so older clients that read the old
    # names continue to work.
    scheduled_start = serializers.DateTimeField(source='start', read_only=True)
    scheduled_end = serializers.DateTimeField(
        source='planned_end', read_only=True
    )
    scheduled_severity = serializers.IntegerField(
        source='severity', read_only=True
    )
    updates = OutageUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = models.Outage
        # Public fields only -- new model fields don't leak by default.
        fields = (
            'id',
            'title',
            'description',
            'start',
            'planned_end',
            'end',
            'severity',
            'severity_display',
            'scheduled',
            'scheduled_display',
            'scheduled_start',
            'scheduled_end',
            'scheduled_severity',
            'status_display',
            'cancelled',
            'updates',
        )


class OutageFilter(rest_filters.FilterSet, filters.ActivityFilterMixin):
    activity = rest_filters.CharFilter(method='filter_activity')

    class Meta:
        model = models.Outage

        fields = {
            'scheduled': ['exact'],
            'cancelled': ['exact'],
            'start': ['exact', 'lt', 'lte', 'gte', 'gt', 'date'],
            'end': ['exact', 'lt', 'lte', 'gte', 'gt', 'date'],
            'planned_end': ['exact', 'lt', 'lte', 'gte', 'gt', 'date'],
            'severity': ['exact', 'in'],
        }


class OutageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OutageSerializer
    filterset_class = OutageFilter
    filter_backends = [rest_filters.DjangoFilterBackend]
    # Public status-page data. Set permission_classes explicitly so the
    # endpoint isn't subject to a future change in the DRF default.
    permission_classes = [permissions.AllowAny]
    pagination_class = OutagePagination

    def get_queryset(self):
        return models.Outage.objects.prefetch_related('updates')
