import zoneinfo

from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.db import transaction
from django import forms
from django.utils import timezone

from langstroth.announcements import models


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


def _resolve_browser_timezone(form, cleaned_data, fields):
    """Reinterpret naive datetime fields in the operator's timezone.

    Django's form field parses naive strings against whatever timezone
    is active for the request, which is unreliable on the first POST
    (tz_detect cookies aren't read yet) and silently shifts the saved
    time by the operator's UTC offset. The browser supplies its IANA
    timezone name via the hidden `tz_name` field; resolve it with
    zoneinfo so the *offset at the field's instant* is used -- a time
    across a DST boundary picks up the offset in force at that time,
    not the offset in force at submission time.
    """
    tz_name = cleaned_data.get('tz_name')
    if not tz_name:
        return True
    try:
        user_tz = zoneinfo.ZoneInfo(tz_name)
    except zoneinfo.ZoneInfoNotFoundError:
        form.add_error(None, f"Unknown browser timezone: {tz_name}")
        return False
    for field in fields:
        dt = cleaned_data.get(field)
        if dt is not None:
            cleaned_data[field] = dt.replace(tzinfo=None).replace(
                tzinfo=user_tz
            )
            setattr(form.instance, field, cleaned_data[field])
    return True


class OutageForm(forms.ModelForm):
    start = forms.DateTimeField(
        required=True,
        widget=DateTimePickerInput(options=PICKER_OPTS),
    )
    planned_end = forms.DateTimeField(
        required=False,
        widget=DateTimePickerInput(range_from='start', options=PICKER_OPTS),
    )
    # Fields for an optional initial AnnouncementUpdate.  Required only when
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
    # Captured client-side via Intl.DateTimeFormat().resolvedOptions()
    # .timeZone -- the operator's IANA timezone name (e.g.
    # "Australia/Melbourne"). Resolved server-side at the *start
    # instant* via zoneinfo, so an outage scheduled across a DST
    # boundary picks up the offset in force at the outage time, not
    # the offset in force at submission time. CharField with explicit
    # max_length: legal IANA names are well under 64 chars.
    tz_name = forms.CharField(
        required=False, max_length=64, widget=forms.HiddenInput()
    )
    # The model field is nullable (null severity is the news marker),
    # so require it and preselect the old model default here.
    severity = forms.TypedChoiceField(
        required=True,
        coerce=int,
        choices=models.SEVERITY_CHOICES,
        initial=models.SIGNIFICANT,
    )

    # Relaxed by NoticeForm: a notice's forecast end is always
    # optional, and a notice may start immediately with just its
    # description.
    require_planned_end_when_scheduled = True
    require_initial_update = True
    category = models.Category.OUTAGE

    class Meta:
        model = models.Announcement
        fields = ['title', 'description', 'start', 'planned_end', 'severity']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set before validation: Model.clean() checks the
        # severity-vs-category invariant on the unsaved instance.
        self.instance.category = self.category
        _apply_bootstrap_classes(self)

    def _is_starting_now(self, start):
        return start <= timezone.now() + models.SCHEDULED_THRESHOLD

    def clean(self):
        cleaned_data = super().clean()
        if not _resolve_browser_timezone(
            self, cleaned_data, ('start', 'planned_end')
        ):
            return cleaned_data
        start = cleaned_data.get('start')
        planned_end = cleaned_data.get('planned_end')

        if start and planned_end and planned_end <= start:
            self.add_error('planned_end', 'Planned end must be after start.')

        if (
            self.require_planned_end_when_scheduled
            and start
            and not self._is_starting_now(start)
            and not planned_end
        ):
            self.add_error(
                'planned_end',
                'Planned end is required for scheduled outages.',
            )

        if (
            self.require_initial_update
            and start
            and self._is_starting_now(start)
        ):
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
        # When creating a starting-now outage, the initial
        # AnnouncementUpdate and the Announcement row must persist
        # together: otherwise a failure
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
                models.AnnouncementUpdate.objects.create(
                    outage=outage,
                    time=timezone.now(),
                    status=cleaned['status'],
                    content=cleaned['content'],
                    created_by=outage.created_by,
                )
        return outage


class NoticeForm(OutageForm):
    """Create a hazard or security notice.

    Same lifecycle machinery as an outage, but a notice's forecast end
    is always optional and it may start immediately with just its
    description (no initial update required).
    """

    require_planned_end_when_scheduled = False
    require_initial_update = False
    category = models.Category.NOTICE


class NewsForm(forms.ModelForm):
    """Create a news item: a lifecycle-free post.

    No severity, planned end, or initial update -- `start` is simply
    the publication time.
    """

    start = forms.DateTimeField(
        required=True,
        label="Publish time",
        initial=timezone.now,
        widget=DateTimePickerInput(options=PICKER_OPTS),
    )
    # Same browser-timezone resolution as OutageForm; see
    # _resolve_browser_timezone.
    tz_name = forms.CharField(
        required=False, max_length=64, widget=forms.HiddenInput()
    )

    class Meta:
        model = models.Announcement
        fields = ['title', 'description', 'start']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set before validation, as in OutageForm.
        self.instance.category = models.Category.NEWS
        _apply_bootstrap_classes(self)

    def clean(self):
        cleaned_data = super().clean()
        _resolve_browser_timezone(self, cleaned_data, ('start',))
        return cleaned_data


class OutageUpdateForm(forms.ModelForm):
    time = forms.DateTimeField(disabled=True)

    class Meta:
        model = models.AnnouncementUpdate
        exclude = ['outage']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _apply_bootstrap_classes(self)

        # RESOLVED is never selectable on an update -- the End action
        # is what marks an outage as resolved (and creates the
        # RESOLVED update itself). Before the first update only
        # investigation-phase statuses make sense. Reopening an ended
        # outage is the only legal action on it via this form, so when
        # outage.end is set restrict the choice to PROGRESSING --
        # otherwise an operator could submit FIXED on a previously
        # resolved outage and leave end set with a non-resolved final
        # update.
        outage = self.initial['outage']
        if outage.end is not None:
            allowed = {models.PROGRESSING}
        elif outage.latest_update is None:
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
