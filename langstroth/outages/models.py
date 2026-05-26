from datetime import timedelta
import logging

from django.db import models
from django.urls import reverse
from django.utils import timezone

from langstroth.models import User

LOG = logging.getLogger(__name__)

# An Outage represents a planned or unplanned service interruption.
#
# `start` and `end` are real timestamps. The outage is in progress when
# `start <= now`, `end is None`, and `cancelled is False`.
#
# `scheduled` is a historical label only -- set on first save based on
# whether `start > now + SCHEDULED_THRESHOLD`. It is never recomputed,
# so the planned-vs-unplanned distinction is preserved after the outage
# begins.
#
# OutageUpdates are operator-authored progress notes. Their `status`
# field tracks investigation phase (INVESTIGATING -> IDENTIFIED ->
# PROGRESSING -> FIXED -> RESOLVED). The outage itself is ended by an
# explicit action that sets `end`; a RESOLVED update may accompany this
# but is not what marks the outage as ended.

# Outage Status
INVESTIGATING = 'IN'
IDENTIFIED = 'ID'
PROGRESSING = 'P'
FIXED = 'F'
RESOLVED = 'R'
STATUS_CHOICES = [
    (INVESTIGATING, 'Investigating'),
    (IDENTIFIED, 'Identified'),
    (PROGRESSING, 'Progressing'),
    (FIXED, 'Fixed'),
    (RESOLVED, 'Resolved'),
]

# Outage Severity
MINIMAL = 1
SIGNIFICANT = 2
SEVERE = 3
SEVERITY_CHOICES = [
    (MINIMAL, 'Minimal'),
    (SIGNIFICANT, 'Significant'),
    (SEVERE, 'Severe'),
]

# An outage is labelled "scheduled" if its start is more than this far
# in the future at creation time.
SCHEDULED_THRESHOLD = timedelta(hours=1)

# Default next status for each current status. Used to pre-fill the
# status field on a new OutageUpdate. RESOLVED -> PROGRESSING enables
# the "reopen" flow (which also clears outage.end in the view).
# FIXED is the terminal investigation status: operators end the outage
# via the End action (which creates a RESOLVED update); they don't
# select RESOLVED from the update form.
STATUS_TRANSITIONS = {
    INVESTIGATING: IDENTIFIED,
    IDENTIFIED: PROGRESSING,
    PROGRESSING: FIXED,
    RESOLVED: PROGRESSING,
}


_STATUS_DISPLAYS = dict(STATUS_CHOICES)
_SEVERITY_DISPLAYS = dict(SEVERITY_CHOICES)


def _status_display(status):
    # Tolerate an unknown code (e.g. legacy row not normalised by migration
    # 0006, or a new status added since): the list view shouldn't crash.
    if status is None:
        return "Unknown"
    return _STATUS_DISPLAYS.get(status, "Unknown")


def _severity_display(severity):
    if severity is None:
        return "Unknown"
    return _SEVERITY_DISPLAYS.get(severity, "Unknown")


class OutageManager(models.Manager):
    def current_outages(self):
        return self.filter(
            cancelled=False,
            start__lte=timezone.now(),
            end__isnull=True,
        ).prefetch_related('updates')


class Outage(models.Model):
    objects = OutageManager()

    title = models.CharField(max_length=255)
    description = models.TextField()
    start = models.DateTimeField()
    # `planned_end` is informational (the announced end of a scheduled
    # window); `end` is the actual end of the outage, set by the End
    # action. Status display keys off `end`, not `planned_end`.
    planned_end = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    severity = models.IntegerField(
        choices=SEVERITY_CHOICES, default=SIGNIFICANT
    )
    scheduled = models.BooleanField(blank=True, default=False, editable=False)
    cancelled = models.BooleanField(blank=True, default=False)
    modification_time = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, editable=False, on_delete=models.PROTECT, related_name='+'
    )
    modified_by = models.ForeignKey(
        User,
        editable=False,
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    class Meta:
        ordering = ['-modification_time']

    def save(self, *args, **kwargs):
        # `scheduled` is a historical label fixed at creation time.
        if self._state.adding and self.start is not None:
            self.scheduled = self.start > timezone.now() + SCHEDULED_THRESHOLD
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("outages:detail", kwargs={'pk': self.pk})

    @property
    def visible_updates(self):
        # Iterate self.updates.all() so prefetch_related('updates') is
        # honoured. Calling get_queryset()/.first()/.last() issues fresh
        # SQL even when the parent was prefetched.
        return list(self.updates.all())

    @property
    def first_update(self):
        updates = self.visible_updates
        return updates[0] if updates else None

    @property
    def latest_update(self):
        updates = self.visible_updates
        return updates[-1] if updates else None

    @property
    def is_current(self):
        return (
            self.start <= timezone.now()
            and self.end is None
            and not self.cancelled
        )

    @property
    def is_upcoming(self):
        return self.start > timezone.now() and not self.cancelled

    @property
    def scheduled_display(self):
        if self.cancelled:
            return "cancelled"
        return "scheduled" if self.scheduled else "unscheduled"

    @property
    def status_display(self):
        if self.cancelled:
            return "Cancelled"
        if self.end:
            return "Completed"
        if self.start > timezone.now():
            return "Scheduled"
        last = self.latest_update
        return last.status_display if last else "In progress"

    @property
    def severity_display(self):
        return _severity_display(self.severity)

    def __str__(self):
        return f"Outage({self.title})"


class OutageUpdate(models.Model):
    time = models.DateTimeField()
    modification_time = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, editable=False, on_delete=models.PROTECT, related_name='+'
    )
    modified_by = models.ForeignKey(
        User,
        editable=False,
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    outage = models.ForeignKey(
        Outage, on_delete=models.CASCADE, related_name="updates"
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    content = models.TextField()

    class Meta:
        ordering = ['time', 'pk']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Bubble activity onto the parent outage so list views ordered
        # by -modification_time surface recent updates. Use a queryset
        # update rather than self.outage.save() to:
        #   * set modified_by (the cascade left it unchanged, so the
        #     parent kept lying about who last touched it),
        #   * bypass auto_now so modification_time matches the update's
        #     own time stamp,
        #   * avoid retriggering Outage.save() side effects.
        actor = self.modified_by or self.created_by
        Outage.objects.filter(pk=self.outage_id).update(
            modification_time=timezone.now(),
            modified_by=actor,
        )

    @property
    def status_display(self):
        return _status_display(self.status)
