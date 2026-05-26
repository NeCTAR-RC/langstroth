from datetime import timedelta

from django import test
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from langstroth import models as auth_models
from langstroth.outages import models


def _make_outage(user, **overrides):
    defaults = {
        "title": "t",
        "description": "d",
        "start": timezone.now() + timedelta(hours=2),
        "severity": models.SIGNIFICANT,
        "created_by": user,
    }
    defaults.update(overrides)
    return models.Outage.objects.create(**defaults)


class ListAndDetailTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )
        cls.outage1 = _make_outage(cls.user, title="one")
        cls.outage2 = _make_outage(
            cls.user, title="two", start=timezone.now() - timedelta(hours=1)
        )

    def test_list(self):
        response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        response = self.client.get(self.outage1.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_list_query_count_bounded(self):
        # Prefetch on the list view means status_display / latest_update
        # do not issue per-row queries. Add another outage with several
        # updates, then assert the query count is independent of how
        # many updates exist -- an N+1 regression would scale with
        # outage_count * update_count.
        outage = _make_outage(
            self.user,
            title="busy",
            start=timezone.now() - timedelta(hours=2),
        )
        for i in range(5):
            models.OutageUpdate.objects.create(
                outage=outage,
                time=timezone.now() - timedelta(minutes=10 - i),
                status=models.INVESTIGATING,
                content=f"update {i}",
                created_by=self.user,
            )
        # 2x COUNT(*) (from the filterset) + 1 list + 1 prefetched
        # updates = 4. If this number drifts upward without an
        # explanation, an N+1 has probably been reintroduced.
        with self.assertNumQueries(4):
            response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)


class CreateOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        cls.enduser = auth_models.User.objects.create(
            username="end", email="end@test.com"
        )

    def test_get_requires_staff(self):
        self.client.force_login(self.enduser)
        response = self.client.get(reverse('outages:create'))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('outages:create'))
        self.assertEqual(response.status_code, 200)

    def test_post_future_start(self):
        self.client.force_login(self.staff)
        future = timezone.now() + timedelta(days=1)
        planned_end = future + timedelta(hours=2)
        response = self.client.post(
            reverse('outages:create'),
            data={
                "title": "Maintenance",
                "description": "Routine",
                "start": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SIGNIFICANT,
                "planned_end": planned_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": "",
                "content": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        outage = models.Outage.objects.get(title="Maintenance")
        self.assertTrue(outage.scheduled)
        self.assertEqual(0, outage.updates.count())

    def test_post_now_start_with_update(self):
        self.client.force_login(self.staff)
        now = timezone.now()
        response = self.client.post(
            reverse('outages:create'),
            data={
                "title": "Broken",
                "description": "Down",
                "start": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SEVERE,
                "planned_end": "",
                "status": models.INVESTIGATING,
                "content": "Outage detected",
            },
        )
        self.assertEqual(response.status_code, 302)
        outage = models.Outage.objects.get(title="Broken")
        self.assertFalse(outage.scheduled)
        self.assertEqual(1, outage.updates.count())


class UpdateAndEndFlowTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        # An in-progress outage (start in the past, no end).
        self.outage = _make_outage(
            self.staff, start=timezone.now() - timedelta(hours=1)
        )

    def _add_update(self, status=models.INVESTIGATING):
        return models.OutageUpdate.objects.create(
            outage=self.outage,
            time=timezone.now(),
            status=status,
            content="x",
            created_by=self.staff,
        )

    def _assert_bad_request(self, response):
        self.assertTemplateUsed(response, "error.html")

    def test_add_update_get(self):
        response = self.client.get(
            reverse('outages:add_update', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_add_update_blocked_when_not_started(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        response = self.client.get(
            reverse('outages:add_update', args=[future.id])
        )
        self._assert_bad_request(response)

    def test_add_update_blocked_when_cancelled(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        future.cancelled = True
        future.save()
        response = self.client.get(
            reverse('outages:add_update', args=[future.id])
        )
        self._assert_bad_request(response)

    def test_add_update_post(self):
        response = self.client.post(
            reverse('outages:add_update', args=[self.outage.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "content": "looking into it",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(1, self.outage.updates.count())

    def test_reopen_clears_end(self):
        # Mark the outage as ended.
        self.outage.end = timezone.now()
        self.outage.save()
        self._add_update(status=models.RESOLVED)

        response = self.client.post(
            reverse('outages:add_update', args=[self.outage.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.PROGRESSING,
                "content": "back open",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNone(self.outage.end)

    def test_end_get(self):
        response = self.client.get(
            reverse('outages:end', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_end_blocked_when_already_ended(self):
        self.outage.end = timezone.now()
        self.outage.save()
        response = self.client.get(
            reverse('outages:end', args=[self.outage.id])
        )
        self._assert_bad_request(response)

    def test_end_blocked_when_not_started(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        response = self.client.get(reverse('outages:end', args=[future.id]))
        self._assert_bad_request(response)

    def test_end_blocked_when_cancelled(self):
        self.outage.cancelled = True
        self.outage.save()
        response = self.client.get(
            reverse('outages:end', args=[self.outage.id])
        )
        self._assert_bad_request(response)

    def test_end_post_sets_end_field(self):
        response = self.client.post(
            reverse('outages:end', args=[self.outage.id]),
            data={"content": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNotNone(self.outage.end)
        self.assertEqual(0, self.outage.updates.count())

    def test_end_post_with_final_note_creates_resolved_update(self):
        response = self.client.post(
            reverse('outages:end', args=[self.outage.id]),
            data={"content": "all clear"},
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNotNone(self.outage.end)
        self.assertEqual(1, self.outage.updates.count())
        update = self.outage.updates.first()
        self.assertEqual(models.RESOLVED, update.status)
        self.assertEqual("all clear", update.content)


class CancelOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )

    def test_cancel_get(self):
        response = self.client.get(
            reverse('outages:cancel', args=[self.future.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_cancel_post(self):
        response = self.client.post(
            reverse('outages:cancel', args=[self.future.id])
        )
        self.assertEqual(response.status_code, 302)
        self.future.refresh_from_db()
        self.assertTrue(self.future.cancelled)

    def test_cancel_blocked_once_started(self):
        started = _make_outage(
            self.staff, start=timezone.now() - timedelta(minutes=1)
        )
        response = self.client.get(
            reverse('outages:cancel', args=[started.id])
        )
        self.assertTemplateUsed(response, "error.html")

    def test_cancel_blocked_when_already_cancelled(self):
        self.future.cancelled = True
        self.future.save()
        response = self.client.get(
            reverse('outages:cancel', args=[self.future.id])
        )
        self.assertTemplateUsed(response, "error.html")


@freeze_time("2024-01-15 12:00:00")
class FilterTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        # Three outages to exercise activity choices.
        cls.upcoming = _make_outage(
            cls.staff,
            title="future",
            start=timezone.now() + timedelta(days=1),
        )
        cls.active = _make_outage(
            cls.staff,
            title="now",
            start=timezone.now() - timedelta(hours=1),
        )
        cls.completed = _make_outage(
            cls.staff,
            title="done",
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() - timedelta(hours=2),
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

    def test_filter_activity_active(self):
        response = self.client.get(
            reverse('outages:list'), {'activity': 'active'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_activity_completed(self):
        response = self.client.get(
            reverse('outages:list'), {'activity': 'completed'}
        )
        self.assertEqual(response.status_code, 200)
