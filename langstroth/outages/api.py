from django.db import models as db_models
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework import viewsets

from langstroth.outages import models


class OutageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OutageUpdate
        fields = ('content', 'time', 'status', 'severity')


class OutageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Outage
        exclude = ('created_by', 'modified_by', 'modification_time',
                   'deleted')

    updates = OutageUpdateSerializer(many=True, read_only=True)


class OutageFilter(filters.FilterSet):

    activity = filters.CharFilter(method='filter_activity')

    def _latest_update(self, queryset):
        """Annotate with the status of the outage's latest update.
        """

        latest_update_status = models.OutageUpdate.objects \
            .filter(outage=db_models.OuterRef('pk')) \
            .order_by('-time', '-id')[:1].values('status')
        return queryset.annotate(
            latest_update_status=db_models.Subquery(latest_update_status))

    def filter_activity(self, queryset, name, value):
        """The filter predicates are:
           'active' => started but not ended
           'ended' => ended
           'overrunning' => started but not ended after scheduled end
           'upcoming' => scheduled in future and not started
           'overdue' => scheduled for now and not started
           'missed' => scheduled in past and never started
        """

        if value == "active":
            return self._latest_update(queryset) \
                       .exclude(latest_update_status__in=
                                [models.COMPLETED, models.RESOLVED])
        elif value == "completed":
            return self._latest_update(queryset) \
                       .filter(latest_update_status__in=
                               [models.COMPLETED, models.RESOLVED])
        elif value == "overrunning":
            return self._latest_update(queryset) \
                       .exclude(latest_update_status__in=
                                [models.COMPLETED, models.RESOLVED]) \
                       .exclude(scheduled_end__gt=timezone.now())

        elif value == "upcoming":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_start__gt=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        elif value == "overdue":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_start__lte=timezone.now(),
                                   scheduled_end__gt=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        elif value == "missed":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_end__lte=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        else:
            # Noop
            return queryset

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
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return models.Outage.objects.filter(deleted=False) \
            .prefetch_related('updates')
