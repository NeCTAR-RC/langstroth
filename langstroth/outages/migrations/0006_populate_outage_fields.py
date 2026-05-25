from django.db import migrations
from django.utils import timezone

# Hardcoded — historical model constants. Don't import from models.py.
STARTED = 'S'
COMPLETED = 'C'
RESOLVED = 'R'
SIGNIFICANT = 2


def populate(apps, schema_editor):
    """Backfill start/end/planned_end/severity from the old fields and updates.

    For every unmigrated outage (start IS NULL):
      - start  = first_update.time, else scheduled_start, else modification_time
      - end    = latest_update.time when its status is RESOLVED or COMPLETED;
                 else (when there are no updates at all) scheduled_end if it
                 is in the past; else None.  Outages with no updates and no
                 past scheduled_end would otherwise appear permanently
                 ongoing, which is wrong for completed-but-never-updated
                 scheduled outages.
      - planned_end = scheduled_end (preserved verbatim -- this is the
                 announced window end, distinct from actual end).
      - severity = latest_update.severity, else scheduled_severity, else
                 leave the column default (SIGNIFICANT).

    Idempotent: skips outages whose `start` is already populated, so a
    second run (e.g. partial migrate on a restored DB) is a no-op rather
    than clobbering operator edits.

    Uses queryset.update() to bypass Outage.modification_time's auto_now,
    so re-anchoring data does not retroactively bump every outage to "most
    recently modified" (Outage.Meta.ordering = ['-modification_time']).

    Then normalise OutageUpdate.status to drop STARTED/COMPLETED:
      - STARTED rows are deleted (their info is now in outage.start).
      - COMPLETED rows become RESOLVED (their time is already in outage.end).
    """
    Outage = apps.get_model('outages', 'Outage')
    OutageUpdate = apps.get_model('outages', 'OutageUpdate')
    now = timezone.now()

    outages = Outage.objects.filter(start__isnull=True).prefetch_related(
        'updates'
    )
    for outage in outages:
        updates = sorted(outage.updates.all(), key=lambda u: (u.time, u.id))
        first = updates[0] if updates else None
        last = updates[-1] if updates else None

        fields = {}

        if first is not None:
            fields['start'] = first.time
        elif outage.scheduled_start is not None:
            fields['start'] = outage.scheduled_start
        else:
            fields['start'] = outage.modification_time

        if last is not None and last.status in (RESOLVED, COMPLETED):
            fields['end'] = last.time
        elif (
            last is None
            and outage.scheduled_end is not None
            and outage.scheduled_end <= now
        ):
            fields['end'] = outage.scheduled_end

        fields['planned_end'] = outage.scheduled_end

        if last is not None:
            fields['severity'] = last.severity
        elif outage.scheduled_severity is not None:
            fields['severity'] = outage.scheduled_severity

        Outage.objects.filter(pk=outage.pk).update(**fields)

    OutageUpdate.objects.filter(status=STARTED).delete()
    OutageUpdate.objects.filter(status=COMPLETED).update(status=RESOLVED)


class Migration(migrations.Migration):
    dependencies = [
        ('outages', '0005_add_new_outage_fields'),
    ]

    operations = [
        migrations.RunPython(populate, reverse_code=migrations.RunPython.noop),
    ]
