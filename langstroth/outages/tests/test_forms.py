from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from langstroth import models as auth_models
from langstroth.outages import models
from langstroth.outages import views  # noqa: F401  break import cycle
from langstroth.outages import forms  # noqa: H306  break import cycle


class UnscheduledOutageFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def test_valid_form_saves_outage_and_initial_update(self):
        now = timezone.now()
        form = forms.UnscheduledOutageForm(
            data={
                "title": "Broken",
                "description": "It's down",
                "time": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SEVERE,
                "status": models.INVESTIGATING,
                "content": "Investigating now",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        # ModelForm.save needs created_by set on the instance first.
        form.instance.created_by = self.user
        outage = form.save()
        self.assertEqual("Broken", outage.title)
        self.assertEqual(1, outage.updates.count())
        update = outage.updates.first()
        self.assertEqual(models.INVESTIGATING, update.status)
        self.assertEqual(models.SEVERE, update.severity)

    def test_form_widget_classes_assigned(self):
        form = forms.UnscheduledOutageForm()
        # Select widgets get 'form-select', the rest get 'form-control'
        self.assertIn(
            'form-select', form.fields['severity'].widget.attrs['class']
        )
        self.assertIn(
            'form-control', form.fields['title'].widget.attrs['class']
        )


class ScheduledOutageFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def _base_data(self, **overrides):
        future = timezone.now() + timedelta(days=1)
        later = future + timedelta(hours=2)
        data = {
            "title": "Maintenance",
            "description": "Routine work",
            "scheduled": True,
            "scheduled_start": future.strftime("%Y-%m-%dT%H:%M:%S"),
            "scheduled_end": later.strftime("%Y-%m-%dT%H:%M:%S"),
            "scheduled_severity": models.SIGNIFICANT,
        }
        data.update(overrides)
        return data

    def test_valid(self):
        form = forms.ScheduledOutageForm(data=self._base_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_widget_classes(self):
        form = forms.ScheduledOutageForm()
        self.assertIn(
            'form-control',
            form.fields['scheduled_start'].widget.attrs['class'],
        )

    def test_missing_start_when_scheduled(self):
        form = forms.ScheduledOutageForm(
            data=self._base_data(scheduled_start='')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_start', form.errors)

    def test_missing_end_when_scheduled(self):
        form = forms.ScheduledOutageForm(
            data=self._base_data(scheduled_end='')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_end', form.errors)

    def test_start_after_end(self):
        future = timezone.now() + timedelta(days=2)
        earlier = timezone.now() + timedelta(days=1)
        form = forms.ScheduledOutageForm(
            data=self._base_data(
                scheduled_start=future.strftime("%Y-%m-%dT%H:%M:%S"),
                scheduled_end=earlier.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_end', form.errors)

    def test_start_in_past(self):
        past = timezone.now() - timedelta(days=1)
        future = timezone.now() + timedelta(days=1)
        form = forms.ScheduledOutageForm(
            data=self._base_data(
                scheduled_start=past.strftime("%Y-%m-%dT%H:%M:%S"),
                scheduled_end=future.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_start', form.errors)

    def test_missing_severity(self):
        form = forms.ScheduledOutageForm(
            data=self._base_data(scheduled_severity='')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_severity', form.errors)

    def test_unscheduled_rejects_scheduled_fields(self):
        future = timezone.now() + timedelta(days=1)
        later = future + timedelta(hours=2)
        form = forms.ScheduledOutageForm(
            data={
                "title": "Maintenance",
                "description": "Routine work",
                "scheduled": False,
                "scheduled_start": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "scheduled_end": later.strftime("%Y-%m-%dT%H:%M:%S"),
                "scheduled_severity": models.SIGNIFICANT,
            }
        )
        self.assertFalse(form.is_valid())


class BaseOutageUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def _make_outage(self, scheduled=False):
        return models.Outage.objects.create(
            scheduled=scheduled,
            title="t",
            description="d",
            created_by=self.user,
        )

    def test_choices_no_update_unscheduled(self):
        outage = self._make_outage(scheduled=False)
        form = forms.BaseOutageUpdateForm(initial={'outage': outage})
        choices = list(form.fields['status'].choices)
        codes = [c[0] for c in choices]
        self.assertIn(models.INVESTIGATING, codes)
        self.assertIn(models.IDENTIFIED, codes)
        self.assertNotIn(models.STARTED, codes)

    def test_choices_no_update_scheduled(self):
        outage = self._make_outage(scheduled=True)
        form = forms.BaseOutageUpdateForm(initial={'outage': outage})
        choices = list(form.fields['status'].choices)
        codes = [c[0] for c in choices]
        self.assertEqual([models.STARTED], codes)

    def test_choices_with_latest_update(self):
        outage = self._make_outage(scheduled=False)
        models.OutageUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            severity=models.SEVERE,
            content="x",
            created_by=self.user,
        )
        form = forms.BaseOutageUpdateForm(initial={'outage': outage})
        codes = [c[0] for c in form.fields['status'].choices]
        # Includes the transition source keys
        self.assertIn(models.INVESTIGATING, codes)


class OutageStartFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

    def _make_outage(self):
        return models.Outage.objects.create(
            scheduled=False,
            title="t",
            description="d",
            created_by=self.user,
        )

    @freeze_time("2024-01-01 12:00:00")
    def test_rejects_future_time(self):
        outage = self._make_outage()
        future = timezone.now() + timedelta(hours=1)
        form = forms.OutageStartForm(
            initial={'outage': outage},
            data={
                "time": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "severity": models.SEVERE,
                "content": "starting",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('time', form.errors)

    @freeze_time("2024-01-01 12:00:00")
    def test_accepts_past_time(self):
        outage = self._make_outage()
        past = timezone.now() - timedelta(hours=1)
        form = forms.OutageStartForm(
            initial={'outage': outage},
            data={
                "time": past.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "severity": models.SEVERE,
                "content": "starting",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
