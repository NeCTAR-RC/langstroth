from django_filters import rest_framework as rest_filters
from rest_framework import serializers
from rest_framework import viewsets

from langstroth.outages import filters
from langstroth.outages import models


class OutageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OutageUpdate
        fields = ('content', 'time', 'status')


class OutageSerializer(serializers.ModelSerializer):
    severity_display = serializers.ReadOnlyField()
    scheduled_display = serializers.ReadOnlyField()
    status_display = serializers.ReadOnlyField()
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

    def get_queryset(self):
        return models.Outage.objects.prefetch_related('updates')
