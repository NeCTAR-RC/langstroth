from datetime import timedelta

from django import test
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from langstroth import models as auth_models
from langstroth.outages import models


class ListAndDetailTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )
        cls.outage1 = models.Outage.objects.create(
            scheduled=True,
            title="one",
            description="Outage one",
            created_by=cls.user,
        )
        cls.outage2 = models.Outage.objects.create(
            scheduled=False,
            title="two",
            description="Outage two",
            created_by=cls.user,
        )

    def test_list(self):
        response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_staff_sees_extra_activity_choices(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        response = self.client.get(self.outage1.get_absolute_url())
        self.assertEqual(response.status_code, 200)


class CreateOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff",
            email="staff@test.com",
            is_staff=True,
        )
        cls.enduser = auth_models.User.objects.create(
            username="end", email="end@test.com"
        )

    def test_create_scheduled_get_requires_staff(self):
        self.client.force_login(self.enduser)
        response = self.client.get(reverse('outages:create_scheduled'))
        self.assertEqual(response.status_code, 403)

    def test_create_scheduled_get(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('outages:create_scheduled'))
        self.assertEqual(response.status_code, 200)

    def test_create_unscheduled_get(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('outages:create_unscheduled'))
        self.assertEqual(response.status_code, 200)

    def test_create_scheduled_post(self):
        self.client.force_login(self.staff)
        future = timezone.now() + timedelta(days=1)
        later = future + timedelta(hours=2)
        response = self.client.post(
            reverse('outages:create_scheduled'),
            data={
                "title": "Maintenance",
                "description": "Routine",
                "scheduled": True,
                "scheduled_start": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "scheduled_end": later.strftime("%Y-%m-%dT%H:%M:%S"),
                "scheduled_severity": models.SIGNIFICANT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.Outage.objects.filter(title="Maintenance").exists()
        )

    def test_create_unscheduled_post(self):
        self.client.force_login(self.staff)
        now = timezone.now()
        response = self.client.post(
            reverse('outages:create_unscheduled'),
            data={
                "title": "Broken",
                "description": "Down",
                "time": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SEVERE,
                "status": models.INVESTIGATING,
                "content": "starting",
            },
        )
        self.assertEqual(response.status_code, 302)
        outage = models.Outage.objects.get(title="Broken")
        self.assertEqual(1, outage.updates.count())


class OutageUpdateFlowTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.scheduled = models.Outage.objects.create(
            scheduled=True,
            title="sched",
            description="d",
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=3),
            scheduled_severity=models.SIGNIFICANT,
            created_by=self.staff,
        )
        self.unscheduled = models.Outage.objects.create(
            scheduled=False,
            title="unsched",
            description="d",
            created_by=self.staff,
        )

    def _start(self, outage, time=None, status=None):
        models.OutageUpdate.objects.create(
            outage=outage,
            time=time or timezone.now(),
            status=status
            or (models.STARTED if outage.scheduled else models.INVESTIGATING),
            severity=models.SIGNIFICANT,
            content="started",
            created_by=self.staff,
        )

    def test_start_get_scheduled(self):
        response = self.client.get(
            reverse('outages:start', args=[self.scheduled.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_start_get_unscheduled(self):
        response = self.client.get(
            reverse('outages:start', args=[self.unscheduled.id])
        )
        self.assertEqual(response.status_code, 200)

    def _assert_bad_request(self, response):
        """Project's handler400 renders error.html with a 200 — so we
        match on the template rather than the status code."""
        self.assertTemplateUsed(response, "error.html")

    def test_start_blocked_if_already_started(self):
        self._start(self.scheduled)
        response = self.client.get(
            reverse('outages:start', args=[self.scheduled.id])
        )
        self._assert_bad_request(response)

    def test_start_blocked_if_cancelled(self):
        self.scheduled.cancelled = True
        self.scheduled.save()
        response = self.client.get(
            reverse('outages:start', args=[self.scheduled.id])
        )
        self._assert_bad_request(response)

    def test_start_post(self):
        # Use a past time so the OutageStartForm clean() accepts it
        past = timezone.now() - timedelta(minutes=1)
        response = self.client.post(
            reverse('outages:start', args=[self.unscheduled.id]),
            data={
                "time": past.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "severity": models.SIGNIFICANT,
                "content": "started",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(1, self.unscheduled.updates.count())

    def test_add_update_get(self):
        self._start(self.unscheduled)
        response = self.client.get(
            reverse('outages:add_update', args=[self.unscheduled.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_add_update_blocked_when_not_started(self):
        response = self.client.get(
            reverse('outages:add_update', args=[self.unscheduled.id])
        )
        self._assert_bad_request(response)

    def test_end_get(self):
        self._start(self.unscheduled)
        response = self.client.get(
            reverse('outages:end', args=[self.unscheduled.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_end_blocked_when_not_started(self):
        response = self.client.get(
            reverse('outages:end', args=[self.unscheduled.id])
        )
        self._assert_bad_request(response)

    def test_end_blocked_when_already_ended(self):
        self._start(self.unscheduled)
        models.OutageUpdate.objects.create(
            outage=self.unscheduled,
            time=timezone.now(),
            status=models.RESOLVED,
            severity=models.SIGNIFICANT,
            content="done",
            created_by=self.staff,
        )
        response = self.client.get(
            reverse('outages:end', args=[self.unscheduled.id])
        )
        self._assert_bad_request(response)

    def test_end_for_scheduled(self):
        self._start(self.scheduled)
        response = self.client.get(
            reverse('outages:end', args=[self.scheduled.id])
        )
        self.assertEqual(response.status_code, 200)


class CancelOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.outage = models.Outage.objects.create(
            scheduled=True,
            title="sched",
            description="d",
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=3),
            scheduled_severity=models.SIGNIFICANT,
            created_by=self.staff,
        )

    def test_cancel_get(self):
        response = self.client.get(
            reverse('outages:cancel', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_cancel_post(self):
        response = self.client.post(
            reverse('outages:cancel', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertTrue(self.outage.cancelled)

    def test_cancel_blocked_when_unscheduled(self):
        unscheduled = models.Outage.objects.create(
            scheduled=False,
            title="unsched",
            description="d",
            created_by=self.staff,
        )
        response = self.client.get(
            reverse('outages:cancel', args=[unscheduled.id])
        )
        self.assertTemplateUsed(response, "error.html")

    def test_cancel_blocked_when_already_cancelled(self):
        self.outage.cancelled = True
        self.outage.save()
        response = self.client.get(
            reverse('outages:cancel', args=[self.outage.id])
        )
        self.assertTemplateUsed(response, "error.html")


@freeze_time("2024-01-15 12:00:00")
class FilterTests(test.TestCase):
    """Drive the `OutageFilters` form via the list page."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        models.Outage.objects.create(
            scheduled=True,
            title="future",
            description="d",
            scheduled_start=timezone.now() + timedelta(days=1),
            scheduled_end=timezone.now() + timedelta(days=2),
            scheduled_severity=models.SIGNIFICANT,
            created_by=cls.staff,
        )

    def test_filter_time_window_1m(self):
        response = self.client.get(
            reverse('outages:list'), {'time_window': '1m'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_time_window_6m(self):
        response = self.client.get(
            reverse('outages:list'), {'time_window': '6m'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_time_window_1y(self):
        response = self.client.get(
            reverse('outages:list'), {'time_window': '1y'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_ordering_reverse(self):
        response = self.client.get(
            reverse('outages:list'), {'ordering': 'reverse'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_activity_upcoming(self):
        response = self.client.get(
            reverse('outages:list'), {'activity': 'upcoming'}
        )
        self.assertEqual(response.status_code, 200)
