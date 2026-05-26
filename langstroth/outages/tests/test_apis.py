from datetime import timedelta
import json

from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework import test

from langstroth import models as auth_models
from langstroth.outages import models


@freeze_time("2012-01-14 14:32:24")
class OutageSimpleTestCase(test.APITestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

        # Outage starting now (unscheduled) with no updates.
        self.one = models.Outage.objects.create(
            title="one",
            description="Outage one",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )

        # Outage with one investigating update.
        self.two = models.Outage.objects.create(
            title="two",
            description="Outage two",
            start=timezone.now(),
            severity=models.SEVERE,
            created_by=self.user,
        )
        models.OutageUpdate.objects.create(
            outage=self.two,
            status=models.INVESTIGATING,
            content="update one",
            time=timezone.now(),
            created_by=self.user,
        )

        self.expected = [
            {
                'scheduled': False,
                'scheduled_display': 'unscheduled',
                'cancelled': False,
                'title': "one",
                'description': "Outage one",
                'end': None,
                'planned_end': None,
                'id': self.one.id,
                'severity': models.SIGNIFICANT,
                'severity_display': 'Significant',
                'start': '2012-01-14T14:32:24Z',
                'status_display': 'In progress',
                'updates': [],
            },
            {
                'scheduled': False,
                'scheduled_display': 'unscheduled',
                'cancelled': False,
                'title': "two",
                'description': "Outage two",
                'end': None,
                'planned_end': None,
                'id': self.two.id,
                'severity': models.SEVERE,
                'severity_display': 'Severe',
                'start': '2012-01-14T14:32:24Z',
                'status_display': 'Investigating',
                'updates': [
                    {
                        'content': 'update one',
                        'status': models.INVESTIGATING,
                        'time': '2012-01-14T14:32:24Z',
                    }
                ],
            },
        ]

    def test_get_unknown(self):
        response = self.client.get("/api/v1/outages/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_known(self):
        self.maxDiff = 1000
        response = self.client.get(f"/api/v1/outages/{self.one.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), self.expected[0])
        response = self.client.get(f"/api/v1/outages/{self.two.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), self.expected[1])

    def test_get_known_redirect(self):
        response = self.client.get(f"/api/v1/outages/{self.one.id}")
        self.assertEqual(
            response.status_code, status.HTTP_301_MOVED_PERMANENTLY
        )
        self.assertEqual(
            response.headers["Location"], f"/api/v1/outages/{self.one.id}/"
        )

    def test_get_all(self):
        self.maxDiff = 1000
        response = self.client.get("/api/v1/outages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'], self.expected)

    def test_get_filtered_cancelled(self):
        response = self.client.get("/api/v1/outages/?cancelled=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)

    def test_get_filtered_severity(self):
        response = self.client.get(
            f"/api/v1/outages/?severity={models.SEVERE}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.two.id)


class OutageFilterTestCase(test.APITestCase):
    """Activity filter behaviour after the refactor.

    Only active / completed / upcoming remain.
    """

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

        now = timezone.now()

        # Active: started, no end.
        self.active = models.Outage.objects.create(
            title="active",
            description="d",
            start=now - timedelta(hours=1),
            severity=models.SEVERE,
            created_by=self.user,
        )

        # Completed: end set.
        self.completed = models.Outage.objects.create(
            title="completed",
            description="d",
            start=now - timedelta(days=1),
            end=now - timedelta(hours=2),
            severity=models.SEVERE,
            created_by=self.user,
        )

        # Upcoming: future start.
        self.upcoming = models.Outage.objects.create(
            title="upcoming",
            description="d",
            start=now + timedelta(days=1),
            severity=models.SEVERE,
            created_by=self.user,
        )

    def test_filter_active(self):
        self._check_activity("active", {self.active.id})

    def test_filter_completed(self):
        self._check_activity("completed", {self.completed.id})

    def test_filter_upcoming(self):
        self._check_activity("upcoming", {self.upcoming.id})

    def test_filter_unknown_returns_all(self):
        self._check_activity(
            "all", {self.active.id, self.completed.id, self.upcoming.id}
        )

    def _check_activity(self, activity, expected_ids):
        response = self.client.get(f"/api/v1/outages/?activity={activity}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual({d['id'] for d in data['results']}, expected_ids)


class OutageFilterLookupTestCase(test.APITestCase):
    """Exercise the `start`/`end`/`planned_end`/`severity` lookup filters
    declared in OutageFilter.Meta.fields (lt/lte/gte/gt/date/in)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="filter-test",
            email="filter@test.com",
            is_superuser=True,
        )
        cls.now = timezone.now().replace(microsecond=0)
        # past: started a week ago, ended two days ago, severe.
        cls.past = models.Outage.objects.create(
            title="past",
            description="d",
            start=cls.now - timedelta(days=7),
            end=cls.now - timedelta(days=2),
            severity=models.SEVERE,
            created_by=cls.user,
        )
        # active: started yesterday, no end, significant.
        cls.active = models.Outage.objects.create(
            title="active",
            description="d",
            start=cls.now - timedelta(days=1),
            severity=models.SIGNIFICANT,
            created_by=cls.user,
        )
        # future: starts tomorrow, planned 2h window, minimal.
        cls.future = models.Outage.objects.create(
            title="future",
            description="d",
            start=cls.now + timedelta(days=1),
            planned_end=cls.now + timedelta(days=1, hours=2),
            severity=models.MINIMAL,
            created_by=cls.user,
        )

    @staticmethod
    def _z(dt):
        # iso8601 with a literal 'Z' tz suffix -- avoids the '+' in
        # `+00:00` being URL-decoded to a space in query strings.
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _ids(self, query):
        response = self.client.get(f"/api/v1/outages/?{query}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        return {d['id'] for d in data['results']}

    def test_start_gte(self):
        cutoff = self._z(self.now - timedelta(hours=2))
        self.assertEqual({self.future.id}, self._ids(f"start__gte={cutoff}"))

    def test_start_lt(self):
        cutoff = self._z(self.now)
        self.assertEqual(
            {self.past.id, self.active.id}, self._ids(f"start__lt={cutoff}")
        )

    def test_start_date(self):
        # start__date filters by the calendar date component only.
        day = (self.now - timedelta(days=1)).date().isoformat()
        self.assertEqual({self.active.id}, self._ids(f"start__date={day}"))

    def test_end_lt(self):
        cutoff = self._z(self.now)
        self.assertEqual({self.past.id}, self._ids(f"end__lt={cutoff}"))

    def test_end_gte_excludes_null(self):
        # gte on end excludes rows with end IS NULL (active + future).
        cutoff = self._z(self.now - timedelta(days=30))
        self.assertEqual({self.past.id}, self._ids(f"end__gte={cutoff}"))

    def test_planned_end_gt(self):
        cutoff = self._z(self.now)
        self.assertEqual(
            {self.future.id}, self._ids(f"planned_end__gt={cutoff}")
        )

    def test_severity_exact(self):
        self.assertEqual(
            {self.past.id}, self._ids(f"severity={models.SEVERE}")
        )

    def test_severity_in(self):
        self.assertEqual(
            {self.past.id, self.future.id},
            self._ids(f"severity__in={models.SEVERE},{models.MINIMAL}"),
        )
