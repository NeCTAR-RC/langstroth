from django_filters import rest_framework as rest_filters
from rest_framework import serializers
from rest_framework import viewsets

from langstroth.outages import filters
from langstroth.outages import models


class OutageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OutageUpdate
        fields = ('content', 'time', 'status', 'severity')


class OutageSerializer(serializers.ModelSerializer):
    severity = serializers.ReadOnlyField()
    severity_display = serializers.ReadOnlyField()
    scheduled_display = serializers.ReadOnlyField()
    status_display = serializers.ReadOnlyField()
    start = serializers.ReadOnlyField()
    end = serializers.ReadOnlyField()

    class Meta:
        model = models.Outage
        exclude = ('created_by', 'modified_by', 'modification_time',
                   'deleted')

    updates = OutageUpdateSerializer(many=True, read_only=True)


class OutageFilter(rest_filters.FilterSet, filters.ActivityFilterMixin):

    activity = rest_filters.CharFilter(method='filter_activity')

    class Meta:
        model = models.Outage

        fields = {
            'scheduled': ['exact'],
            'cancelled': ['exact'],
            'scheduled_start': ['exact', 'lt', 'lte', 'gte', 'gt', 'date'],
            'scheduled_end': ['exact', 'lt', 'lte', 'gte', 'gt', 'date'],
            'scheduled_severity': ['exact', 'in'],
        }


class OutageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OutageSerializer
    filterset_class = OutageFilter
    filter_backends = [rest_filters.DjangoFilterBackend]

    def get_queryset(self):
        return models.Outage.objects.filter(deleted=False) \
            .prefetch_related('updates')
