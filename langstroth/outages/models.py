import logging

from django.db import models
from django.urls import reverse
from django.utils import timezone

from langstroth.models import User

LOG = logging.getLogger(__name__)

# Informally, there are two outage workflows.
#
# For a scheduled outage
#   An Outage is created with scheduled = True and the scheduled start
#     and end date.  Initially there is no OutageUpdate
#   When the outage starts, a STARTED OutageUpdate is added.
#   As the outage continues, OutageUpdates may be added.
#   Finally a COMPLETED OutageUpdates
#
# For an unscheduled outage
#   An Outage is created with scheduled = False.
#   An initial OutageUpdate created immediately.
#   As the outage continues, additional OutageUpdates may be added.
#   Finally a RESOLVED OutageUpdate is added.
#
# The state sequence is flexible:
#   A typical sequence for an unscheduled outage will be INVESTIGATING,
#     IDENTIFIED, PROGRESSING, FIXED, RESOLVED
#   A typical sequence for a scheduled outage will be STARTED, PROGRESSING,
#     COMPLETED.
#   In either case a specific outage may deviate; e.g. skip states, repeat
#     states or return to earlier states.
#
# Records that are marked as deleted will not be shown by user interfaces
# or returned by the APIs.

# Outage Status
STARTED = 'S'
INVESTIGATING = 'IN'
IDENTIFIED = 'ID'
PROGRESSING = 'P'
FIXED = 'F'
RESOLVED = 'R'
COMPLETED = 'C'
STATUS_CHOICES = [
    (STARTED, 'Started'),              # scheduled
    (INVESTIGATING, 'Investigating'),  # unscheduled
    (IDENTIFIED, 'Identified'),        # unscheduled
    (PROGRESSING, 'Progressing'),      # unscheduled or scheduled
    (FIXED, 'Fixed'),                  # unscheduled
    (RESOLVED, 'Resolved'),            # unscheduled
    (COMPLETED, 'Completed'),          # scheduled
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


def _status_display(status):
    if status is None:
        return "Unknown"
    else:
        return [s[1] for s in STATUS_CHOICES if s[0] == status][0]


def _severity_display(severity):
    if severity is None:
        return "Unknown"
    else:
        return [s[1] for s in SEVERITY_CHOICES if s[0] == severity][0]


class OutageManager(models.Manager):
    def current_outages(self):
        query = self.filter(deleted=False, cancelled=False) \
                    .prefetch_related('updates')
        return [o for o in query if o.is_current]


class Outage(models.Model):
    objects = OutageManager()

    title = models.CharField(max_length=255)
    description = models.TextField()
    scheduled = models.BooleanField(blank=True, default=False)
    cancelled = models.BooleanField(blank=True, default=False)
    deleted = models.BooleanField(blank=True, default=False)
    scheduled_start = models.DateTimeField(blank=True, null=True)
    scheduled_end = models.DateTimeField(blank=True, null=True)
    scheduled_severity = models.IntegerField(choices=SEVERITY_CHOICES,
                                             blank=True, null=True)
    modification_time = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, editable=False,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    modified_by = models.ForeignKey(User, editable=False, null=True,
                                    on_delete=models.PROTECT,
                                    related_name='+')

    class Meta:
        ordering = ['-modification_time']

    def get_absolute_url(self):
        return reverse("outages:detail", kwargs={'pk': self.pk})

    @property
    def visible_updates(self):
        return list(self.updates.get_queryset().exclude(deleted=True))

    @property
    def first_update(self):
        return self.updates.get_queryset().exclude(deleted=True).first()

    @property
    def latest_update(self):
        return self.updates.get_queryset().exclude(deleted=True).last()

    @property
    def is_current(self):
        now = timezone.now()
        return ((self.start and not self.end)
                or (self.scheduled
                    and self.scheduled_start
                    and self.scheduled_end
                    and self.scheduled_start < now
                    and self.scheduled_end > now))

    @property
    def start(self):
        first = self.first_update
        return first.time if first else None

    @property
    def end(self):
        last = self.latest_update
        return last.time if last and last.status in {RESOLVED, COMPLETED} \
            else None

    @property
    def scheduled_display(self):
        return "cancelled" if self.cancelled \
            else "scheduled" if self.scheduled else "unscheduled"

    @property
    def status_display(self):
        last = self.latest_update
        if self.scheduled:
            return "Scheduled" if not last \
                else "Completed" if last.status in {RESOLVED, COMPLETED} \
                else "In progress"
        else:
            return last.status_display if last else "Unknown"

    @property
    def severity_display(self):
        last = self.latest_update
        severity = last.severity if last else self.scheduled_severity
        return _severity_display(severity)

    @property
    def severity(self):
        last = self.latest_update
        return last.severity if last \
            else self.scheduled_severity or SIGNIFICANT

    def __str__(self):
        return f"Outage({self.title})"


class OutageUpdate(models.Model):
    time = models.DateTimeField()
    modification_time = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, editable=False,
                                   on_delete=models.PROTECT,
                                   related_name='+')
    modified_by = models.ForeignKey(User, editable=False, null=True,
                                    on_delete=models.PROTECT,
                                    related_name='+')
    outage = models.ForeignKey(Outage, on_delete=models.CASCADE,
                               related_name="updates")
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    content = models.TextField()
    deleted = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ['time', 'pk']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.outage.save()

    @property
    def status_display(self):
        return _status_display(self.status)

    @property
    def severity_display(self):
        return _severity_display(self.severity)
