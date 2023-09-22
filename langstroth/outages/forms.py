from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.core.exceptions import ValidationError
from django import forms
from django.utils import timezone

from langstroth.outages import models


class OutageForm(forms.ModelForm):
    scheduled_start = forms.DateTimeField(
        required=False, widget=DateTimePickerInput())
    scheduled_end = forms.DateTimeField(
        required=False, widget=DateTimePickerInput())

    class Meta:
        model = models.Outage
        exclude = ['deleted', 'cancelled', 'created_by', 'updated_by',
                   'modification_time']

    def clean(self):
        cleaned_data = super().clean()
        scheduled = cleaned_data.get("scheduled")
        start = cleaned_data.get("scheduled_start")
        end = cleaned_data.get("scheduled_end")
        severity = cleaned_data.get("scheduled_severity")
        if scheduled:
            if not start:
                self.add_error("scheduled_start",
                               "Scheduled start date & time is required")
            if not end:
                self.add_error("scheduled_end",
                               "Scheduled end date & time is required")
            if start and end and start >= end:
                self.add_error("scheduled_end",
                               "Scheduled start must be before end!")
            if start and start < timezone.now():
                self.add_error("scheduled_start",
                               "Scheduled start is in the past!")
            if not severity:
                self.add_error("scheduled_severity",
                               "Scheduled severity is required")
        else:
            if start or end or severity:
                raise ValidationError("start, end or severity not None")


class BaseOutageUpdateForm(forms.ModelForm):
    outage = forms.ModelChoiceField(
        queryset=models.Outage.objects.exclude(deleted=True),
        widget=forms.HiddenInput())

    class Meta:
        model = models.OutageUpdate
        fields = '__all__'


class OutageUpdateForm(BaseOutageUpdateForm):
    time = forms.DateTimeField(disabled=True)


class OutageStartForm(OutageUpdateForm):
    time = forms.DateTimeField(
        required=False, widget=DateTimePickerInput())

    def clean(self):
        cleaned_data = super().clean()
        time = cleaned_data.get("time")
        # A start update 'time' in the future is not allowed because we show
        # them in 'time' order, and because the of the logic for determining
        # the current outage state and severity depends on that ordering.
        if time > timezone.now():
            self.add_error("time",
                           "Outage start date & time is in the future! "
                           "If this is a scheduled outage and you need "
                           "to start it ahead of its scheduled start, "
                           "you should set this field to the actual outage "
                           "start time.")
