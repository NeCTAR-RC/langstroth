from datetime import datetime
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

        self.times = [timezone.now()]

        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com",
            is_superuser=True)

        self.one = models.Outage.objects.create(
            scheduled=False, title="one", description="Outage one",
            created_by=self.user)

        self.two = models.Outage.objects.create(
            scheduled=False, title="two", description="Outage two",
            created_by=self.user)
        models.OutageUpdate.objects.create(
            outage=self.two,
            status=models.INVESTIGATING,
            severity=models.SEVERE,
            content="update one",
            time=self.times[0],
            created_by=self.user
        )

        self.expected = [
            {'scheduled': False,
             'scheduled_display': 'unscheduled',
             'cancelled': False,
             'title': "one",
             'description': "Outage one",
             'end': None,
             'id': self.one.id,
             'scheduled_start': None,
             'scheduled_end': None,
             'scheduled_severity': None,
             'severity': models.SIGNIFICANT,
             'severity_display': 'Unknown',
             'start': None,
             'status_display': 'Investigating',
             'updates': []},
            {'scheduled': False,
             'scheduled_display': 'unscheduled',
             'cancelled': False,
             'title': "two",
             'description': "Outage two",
             'end': None,
             'id': self.two.id,
             'scheduled_start': None,
             'scheduled_end': None,
             'scheduled_severity': None,
             'severity': models.SEVERE,
             'severity_display': 'Severe',
             'start': '2012-01-14T14:32:24Z',
             'status_display': 'Investigating',
             'updates': [{
                 'content': 'update one',
                 'severity': models.SEVERE,
                 'status': models.INVESTIGATING,
                 'time': datetime.isoformat(
                     timezone.localtime(self.times[0]),
                     timespec='auto')}]
            }]

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
        self.assertEqual(json.loads(response.content),
                         self.expected[1])

    def test_get_known_redirect(self):
        response = self.client.get(f"/api/v1/outages/{self.one.id}")
        self.assertEqual(response.status_code,
                         status.HTTP_301_MOVED_PERMANENTLY)
        self.assertEqual(response.headers["Location"],
                         f"/api/v1/outages/{self.one.id}/")

    def test_get_all(self):
        self.maxDiff = 1000
        # Get all with no filtering
        response = self.client.get("/api/v1/outages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data, self.expected)

    def test_get_filtered(self):
        # Just a simple filter based on a plain field
        response = self.client.get("/api/v1/outages/?cancelled=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)


class OutageFilterTestCase(test.APITestCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.times = [
            timezone.now() + timedelta(days=i) for i in range(-3, 4, 2)]

        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com",
            is_superuser=True)
        self.user.save()

        self.past = models.Outage.objects.create(
            scheduled=True, title="past", description="Outage one",
            scheduled_start=self.times[0], scheduled_end=self.times[1],
            scheduled_severity=models.SEVERE,
            created_by=self.user)
        self.past.save()

        self.current = models.Outage.objects.create(
            scheduled=True, title="past", description="Outage two",
            scheduled_start=self.times[1], scheduled_end=self.times[2],
            scheduled_severity=models.SEVERE,
            created_by=self.user)
        self.current.save()

        self.future = models.Outage.objects.create(
            scheduled=True, title="future", description="Outage three",
            scheduled_start=self.times[2], scheduled_end=self.times[3],
            created_by=self.user)
        self.future.save()

    def test_get_upcoming(self):
        self._check_activity("upcoming", [self.future])

    def test_get_overdue(self):
        self._check_activity("overdue", [self.current])

    def test_get_missed(self):
        self._check_activity("missed", [self.past])

    def test_get_active_and_completed(self):
        # Initially, no updates => nothing started, nothing completed
        self._check_activity("completed", [])
        self._check_activity("active", [])
        self._check_activity("overrunning", [])

        # Start the "current" outage
        models.OutageUpdate.objects.create(
            outage=self.current, time=self.times[1],
            modification_time=self.times[1], created_by=self.user,
            severity=models.SEVERE, status=models.STARTED,
            content="yadda")

        self._check_activity("completed", [])
        self._check_activity("active", [self.current])
        self._check_activity("overrunning", [])

        # Complete the "current" outage
        later = self.times[1] + timedelta(hours=1)
        models.OutageUpdate.objects.create(
            outage=self.current, time=later,
            modification_time=later, created_by=self.user,
            severity=models.SEVERE, status=models.COMPLETED,
            content="yadda")

        self._check_activity("completed", [self.current])
        self._check_activity("active", [])
        self._check_activity("overrunning", [])

        # Start the "past" outage
        models.OutageUpdate.objects.create(
            outage=self.past, time=self.times[0],
            modification_time=self.times[0], created_by=self.user,
            severity=models.SEVERE, status=models.STARTED,
            content="yadda")

        self._check_activity("completed", [self.current])
        self._check_activity("active", [self.past])
        self._check_activity("overrunning", [self.past])

        # Complete the "past" outage
        later = self.times[0] + timedelta(hours=1)
        models.OutageUpdate.objects.create(
            outage=self.past, time=later,
            modification_time=later, created_by=self.user,
            severity=models.SEVERE, status=models.COMPLETED,
            content="yadda")

        self._check_activity("completed", [self.past, self.current])
        self._check_activity("active", [])
        self._check_activity("overrunning", [])

    def _check_activity(self, activity, expected):
        """Run an activity filter and check what outage ids it returns.
        """

        response = self.client.get(
            f"/api/v1/outages/?activity={activity}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), len(expected))
        for i in range(0, len(expected)):
            self.assertEqual(data[i]['id'], expected[i].id)
