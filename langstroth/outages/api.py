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


class OutageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OutageSerializer

    def get_queryset(self):
        return models.Outage.objects.filter(deleted=False)
