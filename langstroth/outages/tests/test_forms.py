from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from langstroth import models as auth_models
from langstroth.outages import forms
from langstroth.outages import models


class OutageFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def _data(self, **overrides):
        start = timezone.now() + timedelta(days=1)
        planned_end = start + timedelta(hours=2)
        data = {
            "title": "Maintenance",
            "description": "Routine work",
            "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "severity": models.SIGNIFICANT,
            "planned_end": planned_end.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "",
            "content": "",
            "tz_offset": "",
        }
        data.update(overrides)
        return data

    def test_future_start_no_initial_update(self):
        form = forms.OutageForm(data=self._data())
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        self.assertEqual(0, outage.updates.count())
        self.assertTrue(outage.scheduled)

    def test_now_start_requires_status_and_content(self):
        start = timezone.now()
        form = forms.OutageForm(
            data=self._data(start=start.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
        self.assertIn('content', form.errors)

    def test_now_start_with_initial_update(self):
        start = timezone.now()
        form = forms.OutageForm(
            data=self._data(
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                status=models.INVESTIGATING,
                content="Outage detected",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        self.assertEqual(1, outage.updates.count())
        update = outage.updates.first()
        self.assertEqual(models.INVESTIGATING, update.status)
        self.assertEqual("Outage detected", update.content)
        self.assertFalse(outage.scheduled)

    def test_past_start_treated_as_starting_now(self):
        # A "starting now" outage with a slightly past start still
        # requires the initial update fields.
        start = timezone.now() - timedelta(minutes=5)
        form = forms.OutageForm(
            data=self._data(start=start.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_scheduled_outage_requires_planned_end(self):
        # A scheduled outage (start > now + 1h) must specify a planned
        # end. Without it, the form should be invalid.
        scheduled_start = timezone.now() + timedelta(hours=4)
        form = forms.OutageForm(
            data=self._data(
                start=scheduled_start.strftime("%Y-%m-%dT%H:%M:%S"),
                planned_end="",
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn('planned_end', form.errors)

    def test_starting_now_outage_does_not_require_planned_end(self):
        # An unscheduled / starting-now outage doesn't need a planned
        # end -- end is stamped when the operator ends it.
        start = timezone.now()
        form = forms.OutageForm(
            data=self._data(
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                planned_end="",
                status=models.INVESTIGATING,
                content="starting",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_planned_end_must_be_after_start(self):
        start = timezone.now() + timedelta(days=1)
        planned_end = start - timedelta(hours=1)
        form = forms.OutageForm(
            data=self._data(
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                planned_end=planned_end.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn('planned_end', form.errors)

    def test_tz_offset_reinterprets_naive_datetime(self):
        # Regression: operator in AEST (UTC+10) typing "14:40" should
        # have it stored as 04:40 UTC, not 14:40 UTC. Without the
        # tz_offset hidden field, Django parses naive datetime against
        # the currently-active timezone (UTC by default), silently
        # shifting the saved time by the operator's UTC offset.
        local_now = timezone.now() + timedelta(hours=10)  # AEST-ish local
        local_naive_str = local_now.replace(tzinfo=None).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        form = forms.OutageForm(
            data=self._data(
                start=local_naive_str,
                tz_offset=600,  # AEST = UTC+10 = 600 min east
                status=models.INVESTIGATING,
                content="starting",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        # After reinterpretation, the stored UTC time should match the
        # current server UTC time (within seconds).
        diff = abs((outage.start - timezone.now()).total_seconds())
        self.assertLess(diff, 5, f"start {outage.start} != now")
        self.assertTrue(outage.is_current)

    def test_no_tz_offset_falls_back_to_active_timezone(self):
        # If the browser didn't supply tz_offset (e.g. JS disabled),
        # the form falls back to Django's normal parsing -- the value
        # is treated as being in the request's active timezone.
        start = timezone.now() + timedelta(hours=2)
        form = forms.OutageForm(
            data=self._data(
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        self.assertEqual(start.replace(microsecond=0), outage.start)
        self.assertTrue(outage.is_upcoming)

    def test_future_start_with_planned_end_is_not_completed(self):
        # Regression: filling in planned_end on creation must NOT mark
        # the outage as completed -- planned_end is informational, end
        # is the actual end of the outage.
        start = timezone.now() + timedelta(days=1)
        planned_end = start + timedelta(hours=2)
        form = forms.OutageForm(
            data=self._data(
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                planned_end=planned_end.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        self.assertIsNone(outage.end)
        self.assertEqual(
            planned_end.replace(microsecond=0), outage.planned_end
        )
        self.assertEqual("Scheduled", outage.status_display)

    def test_scheduled_label_set_on_creation_and_frozen(self):
        # Start more than 1 hour in the future -> scheduled=True.
        start = timezone.now() + timedelta(hours=4)
        form = forms.OutageForm(
            data=self._data(start=start.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.user
        outage = form.save()
        self.assertTrue(outage.scheduled)

        # Subsequent save does NOT recompute scheduled even if start
        # is now in the past.
        outage.start = timezone.now() - timedelta(hours=1)
        outage.save()
        outage.refresh_from_db()
        self.assertTrue(outage.scheduled)

    def test_widget_classes(self):
        form = forms.OutageForm()
        self.assertIn(
            'form-control', form.fields['title'].widget.attrs['class']
        )
        self.assertIn(
            'form-select', form.fields['severity'].widget.attrs['class']
        )


class OutageUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def _make_outage(self):
        return models.Outage.objects.create(
            title="t",
            description="d",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )

    def test_choices_no_updates(self):
        outage = self._make_outage()
        form = forms.OutageUpdateForm(initial={'outage': outage})
        codes = [c[0] for c in form.fields['status'].choices]
        self.assertEqual({models.INVESTIGATING, models.IDENTIFIED}, set(codes))

    def test_choices_with_latest_update_excludes_resolved(self):
        # RESOLVED is reachable only via the End action, so the update
        # form must not offer it as a choice.
        outage = self._make_outage()
        models.OutageUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.user,
        )
        form = forms.OutageUpdateForm(initial={'outage': outage})
        codes = {c[0] for c in form.fields['status'].choices if c[0]}
        self.assertEqual(
            {
                models.INVESTIGATING,
                models.IDENTIFIED,
                models.PROGRESSING,
                models.FIXED,
            },
            codes,
        )
        self.assertNotIn(models.RESOLVED, codes)


class OutageEndFormTests(TestCase):
    def test_empty_is_valid(self):
        form = forms.OutageEndForm(data={'content': ''})
        self.assertTrue(form.is_valid(), form.errors)

    def test_with_content_is_valid(self):
        form = forms.OutageEndForm(data={'content': 'all clear'})
        self.assertTrue(form.is_valid(), form.errors)


class FrozenScheduledLabelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="t", email="t@t.com", is_superuser=True
        )

    @freeze_time("2024-01-01 12:00:00")
    def test_scheduled_true_when_start_far_in_future(self):
        outage = models.Outage.objects.create(
            title="t",
            description="d",
            start=timezone.now() + timedelta(hours=2),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        self.assertTrue(outage.scheduled)

    @freeze_time("2024-01-01 12:00:00")
    def test_scheduled_false_when_start_within_threshold(self):
        outage = models.Outage.objects.create(
            title="t",
            description="d",
            start=timezone.now() + timedelta(minutes=30),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        self.assertFalse(outage.scheduled)
