from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.core.exceptions import ValidationError
from django import forms
from django.utils import timezone

from langstroth.outages import models
from langstroth.outages import views


class OutageForm(forms.ModelForm):
    scheduled_start = forms.DateTimeField(
        required=False, widget=DateTimePickerInput())
    scheduled_end = forms.DateTimeField(
        required=False, widget=DateTimePickerInput())

    class Meta:
        model = models.Outage
        exclude = ['deleted', 'cancelled']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'input_type') \
               and field.widget.input_type == 'select':
                field.widget.attrs['class'] = (
                    'form-select ' + field.widget.attrs.get('class', ''))
            else:
                field.widget.attrs['class'] = (
                    'form-control ' + field.widget.attrs.get('class', ''))

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

    class Meta:
        model = models.OutageUpdate
        exclude = ['outage']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for field in self.fields.values():
            if hasattr(field.widget, 'input_type') \
               and field.widget.input_type == 'select':
                field.widget.attrs['class'] = (
                    'form-select ' + field.widget.attrs.get('class', ''))
            else:
                field.widget.attrs['class'] = (
                    'form-control ' + field.widget.attrs.get('class', ''))

        # Filter the choices for the 'status' field.  This is intended to
        # avoid non-sensical transitions but still to give operators
        # plenty of flexibility.

        outage = self.initial['outage']
        latest = outage.latest_update
        if latest:
            allowed_choices = \
                views.STATUS_TRANSITIONS[outage.scheduled].keys()
        elif outage.scheduled:
            allowed_choices = [models.STARTED]
        else:
            allowed_choices = [models.INVESTIGATING, models.IDENTIFIED]
        self.fields['status'].choices = (
            choice for choice in self.fields['status'].choices
            if choice[0] in allowed_choices)


class OutageUpdateForm(BaseOutageUpdateForm):
    time = forms.DateTimeField(disabled=True)


class OutageStartForm(OutageUpdateForm):
    time = forms.DateTimeField(
        required=True, widget=DateTimePickerInput())

    def clean(self):
        cleaned_data = super().clean()
        time = cleaned_data.get("time")
        # A start update 'time' in the future is not allowed because we show
        # them in 'time' order, and because the of the logic for determining
        # the current outage state and severity depends on that ordering.
        if time and time > timezone.now():
            self.add_error("time",
                           "Outage start date & time is in the future! "
                           "If this is a scheduled outage and you need "
                           "to start it ahead of its scheduled start, "
                           "you should set this field to the actual outage "
                           "start time.")
