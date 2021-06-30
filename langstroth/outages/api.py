from django.conf import settings
#from django_filters import rest_framework as filters
from rest_framework import decorators
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import response
from rest_framework import serializers
from rest_framework import status
from rest_framework import viewsets

from langstroth.outages import models


class OutageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Outage
        fields = '__all__'


class OutageViewSet(viewsets.ModelViewSet):
    queryset = models.Outage.objects.all()
    serializer_class = OutageSerializer
