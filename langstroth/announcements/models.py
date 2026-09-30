from datetime import timedelta
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from langstroth.models import User

LOG = logging.getLogger(__name__)

# An Announcement (historically "Outage") is one of three categories,
# discriminated by `category`:
#
#   outage -- a planned or unplanned service interruption.
#   notice -- a hazard or security notice (e.g. a CVE advisory, or a
#             heatwave that may affect DC cooling). Same lifecycle as
#             an outage: severity, a real window, operator updates;
#             the End action means the notice is "stood down".
#   news   -- a lifecycle-free post (feature release, component
#             upgrade). `start` is the publication time;
#             `planned_end`, `end` and `severity` are always null; it
#             has no updates and no state machine. News is never
#             "active" (see filters.ActivityFilterMixin) -- it is
#             discovered by recency.
#
# For outages and notices:
#
# `start` and `end` are real timestamps. The outage is in progress when
# `start <= now`, `end is None`, and `cancelled is False`.
#
# `scheduled` is a historical label only -- set on first save based on
# whether `start > now + SCHEDULED_THRESHOLD`. It is never recomputed,
# so the planned-vs-unplanned distinction is preserved after the outage
# begins.
#
# AnnouncementUpdates are operator-authored progress notes. Their
# `status` field tracks investigation phase (INVESTIGATING ->
# IDENTIFIED -> PROGRESSING -> FIXED -> RESOLVED). The outage itself is
# ended by an explicit action that sets `end`; a RESOLVED update may
# accompany this but is not what marks the outage as ended.

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


class Category(models.TextChoices):
    OUTAGE = 'outage', 'Outage'
    NEWS = 'news', 'News'
    NOTICE = 'notice', 'Notice'


# An outage is labelled "scheduled" if its start is more than this far
# in the future at creation time.
SCHEDULED_THRESHOLD = timedelta(hours=1)

# Default next status for each current status. Used to pre-fill the
# status field on a new AnnouncementUpdate. RESOLVED -> PROGRESSING enables
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
    # None is legitimate (news rows have no severity); only an
    # unrecognised code is "Unknown".
    if severity is None:
        return None
    return _SEVERITY_DISPLAYS.get(severity, "Unknown")


class AnnouncementManager(models.Manager):
    def current(self):
        # Ongoing outages and notices. News is lifecycle-free (`end`
        # is always null), so without the exclusion every news item
        # would be "current" forever.
        return (
            self.filter(
                cancelled=False,
                start__lte=timezone.now(),
                end__isnull=True,
            )
            .exclude(category=Category.NEWS)
            .prefetch_related('updates')
        )

    def upcoming(self):
        """Not-yet-started outages and notices, soonest first.

        News is excluded: a future `start` there is a scheduled
        publication, not an upcoming event. No updates prefetch --
        `status_display` short-circuits to "Scheduled" for these rows,
        so templates never touch `latest_update`.
        """
        return (
            self.filter(cancelled=False, start__gt=timezone.now())
            .exclude(category=Category.NEWS)
            .order_by('start')
        )

    def recently_ended(self, days=30):
        """Outages and notices that ended within the last `days`,
        most recently ended first.

        `end__gte` naturally excludes news (its `end` is always null)
        and cancelled rows (Cancel is only allowed before start and
        End refuses cancelled rows, so `end` is never set on them).
        No updates prefetch -- `status_display` short-circuits to
        "Completed" for ended rows.
        """
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(end__gte=cutoff).order_by('-end')


class Announcement(models.Model):
    objects = AnnouncementManager()

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=10, choices=Category.choices, default=Category.OUTAGE
    )
    # For news, `start` is the publication time.
    start = models.DateTimeField()
    # `planned_end` is informational (the announced end of a scheduled
    # window); `end` is the actual end of the outage, set by the End
    # action. Status display keys off `end`, not `planned_end`.
    # Both are always null for news.
    planned_end = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    # Null exactly when category is news; see clean().
    severity = models.IntegerField(
        choices=SEVERITY_CHOICES, blank=True, null=True
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

    def clean(self):
        # Enforced here (rather than only in the create forms) so the
        # admin -- the de facto edit UI -- upholds the invariant too.
        # The whole news invariant matters: recently_ended() relies
        # on news never having `end`/`planned_end`.
        if self.category == Category.NEWS:
            errors = {}
            if self.severity is not None:
                errors['severity'] = "News must not have a severity."
            if self.planned_end is not None:
                errors['planned_end'] = (
                    "News is lifecycle-free and must not have a "
                    "planned end. Retract it by setting cancelled."
                )
            if self.end is not None:
                errors['end'] = (
                    "News is lifecycle-free and must not have an "
                    "end. Retract it by setting cancelled."
                )
            if errors:
                raise ValidationError(errors)
        elif self.severity is None:
            raise ValidationError(
                {'severity': "Outages and notices require a severity."}
            )

    def get_absolute_url(self):
        return reverse("announcements:detail", kwargs={'pk': self.pk})

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
        if self.category == Category.NEWS:
            # `cancelled` on news means retracted (admin-only action).
            return "Retracted" if self.cancelled else "Published"
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
        return f"Announcement({self.title})"


class AnnouncementUpdate(models.Model):
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
        Announcement, on_delete=models.CASCADE, related_name="updates"
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    content = models.TextField()

    class Meta:
        ordering = ['time', 'pk']

    def clean(self):
        # News is lifecycle-free: no updates, ever. The web views
        # refuse this; enforce it for the admin inline too.
        if self.outage_id and self.outage.category == Category.NEWS:
            raise ValidationError("News must not have updates.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Bubble activity onto the parent outage so list views ordered
        # by -modification_time surface recent updates. Use a queryset
        # update rather than self.outage.save() to:
        #   * set modified_by (the cascade left it unchanged, so the
        #     parent kept lying about who last touched it),
        #   * bypass auto_now so modification_time matches the update's
        #     own time stamp,
        #   * avoid retriggering Announcement.save() side effects.
        actor = self.modified_by or self.created_by
        Announcement.objects.filter(pk=self.outage_id).update(
            modification_time=timezone.now(),
            modified_by=actor,
        )

    @property
    def status_display(self):
        return _status_display(self.status)
