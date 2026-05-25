from datetime import timedelta, timezone as dt_timezone

from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.db import transaction
from django import forms
from django.utils import timezone

from langstroth.outages import models


PICKER_OPTS = {
    'showTodayButton': True,
    'showClear': True,
    'format': 'MM/DD/YYYY HH:mm',
}


def _apply_bootstrap_classes(form):
    for field in form.fields.values():
        if (
            hasattr(field.widget, 'input_type')
            and field.widget.input_type == 'select'
        ):
            field.widget.attrs['class'] = (
                'form-select ' + field.widget.attrs.get('class', '')
            )
        else:
            field.widget.attrs['class'] = (
                'form-control ' + field.widget.attrs.get('class', '')
            )


class OutageForm(forms.ModelForm):
    start = forms.DateTimeField(
        required=True,
        widget=DateTimePickerInput(options=PICKER_OPTS),
    )
    planned_end = forms.DateTimeField(
        required=False,
        widget=DateTimePickerInput(range_from='start', options=PICKER_OPTS),
    )
    # Fields for an optional initial OutageUpdate.  Required only when
    # `start <= now + threshold` -- i.e. the outage is starting now (or
    # has already started).
    status = forms.ChoiceField(
        required=False,
        choices=[('', '---')]
        + [
            choice
            for choice in models.STATUS_CHOICES
            if choice[0] in (models.INVESTIGATING, models.IDENTIFIED)
        ],
    )
    content = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
    # Captured client-side: minutes east of UTC for the user's browser
    # at submission time. Used to reinterpret the naive datetime-local
    # values as the operator's timezone, independent of which timezone
    # Django happens to have activated for the request.
    tz_offset = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = models.Outage
        fields = ['title', 'description', 'start', 'planned_end', 'severity']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _apply_bootstrap_classes(self)

    def _is_starting_now(self, start):
        return start <= timezone.now() + models.SCHEDULED_THRESHOLD

    def clean(self):
        cleaned_data = super().clean()
        # Reinterpret datetime fields in the operator's timezone if the
        # browser supplied its offset. Django's form field parses
        # naive strings against whatever timezone is active for the
        # request, which is unreliable on the first POST (tz_detect
        # cookies aren't read yet) and silently shifts the saved time
        # by the operator's UTC offset.
        offset_min = cleaned_data.get('tz_offset')
        if offset_min is not None:
            user_tz = dt_timezone(timedelta(minutes=offset_min))
            for field in ('start', 'planned_end'):
                dt = cleaned_data.get(field)
                if dt is not None:
                    cleaned_data[field] = dt.replace(tzinfo=None).replace(
                        tzinfo=user_tz
                    )
                    setattr(self.instance, field, cleaned_data[field])
        start = cleaned_data.get('start')
        planned_end = cleaned_data.get('planned_end')

        if start and planned_end and planned_end <= start:
            self.add_error('planned_end', 'Planned end must be after start.')

        if start and not self._is_starting_now(start) and not planned_end:
            self.add_error(
                'planned_end',
                'Planned end is required for scheduled outages.',
            )

        if start and self._is_starting_now(start):
            if not cleaned_data.get('status'):
                self.add_error(
                    'status',
                    'Status is required when the outage is starting now.',
                )
            if not cleaned_data.get('content'):
                self.add_error(
                    'content',
                    'An initial update message is required when the '
                    'outage is starting now.',
                )
        return cleaned_data

    def save(self, commit=True):
        cleaned = self.cleaned_data
        # When creating a starting-now outage, the initial OutageUpdate
        # and the Outage row must persist together: otherwise a failure
        # creating the update leaves a started outage with no update
        # and `status_display` lies.
        with transaction.atomic():
            outage = super().save(commit=commit)
            if (
                commit
                and self._is_starting_now(outage.start)
                and cleaned.get('status')
                and cleaned.get('content')
            ):
                models.OutageUpdate.objects.create(
                    outage=outage,
                    time=timezone.now(),
                    status=cleaned['status'],
                    content=cleaned['content'],
                    created_by=outage.created_by,
                )
        return outage


class OutageUpdateForm(forms.ModelForm):
    time = forms.DateTimeField(disabled=True)

    class Meta:
        model = models.OutageUpdate
        exclude = ['outage']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _apply_bootstrap_classes(self)

        # RESOLVED is never selectable on an update -- the End action
        # is what marks an outage as resolved (and creates the
        # RESOLVED update itself). Before the first update only
        # investigation-phase statuses make sense.
        outage = self.initial['outage']
        if outage.latest_update is None:
            allowed = {models.INVESTIGATING, models.IDENTIFIED}
        else:
            allowed = {
                models.INVESTIGATING,
                models.IDENTIFIED,
                models.PROGRESSING,
                models.FIXED,
            }
        self.fields['status'].choices = [
            choice
            for choice in self.fields['status'].choices
            if choice[0] in allowed
        ]


class OutageEndForm(forms.Form):
    content = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label='Final update (optional)',
        help_text=(
            "If provided, this becomes a RESOLVED update on the outage."
        ),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _apply_bootstrap_classes(self)
