from datetime import datetime
import json

from django.utils import timezone
from rest_framework import status
from rest_framework import test

from langstroth import models as auth_models
from langstroth.outages import models


class OutageGetTestCase(test.APITestCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.times = [timezone.now()]

        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com",
            is_superuser=True)
        self.user.save()

        self.one = models.Outage.objects.create(
            scheduled=False, title="one", description="Outage one",
            created_by=self.user)
        self.one.save()

        self.two = models.Outage.objects.create(
            scheduled=False, title="two", description="Outage two",
            created_by=self.user)
        self.two.save()
        models.OutageUpdate.objects.create(
            outage=self.two,
            status=models.INVESTIGATING,
            severity=models.SEVERE,
            content="update one",
            time=self.times[0],
            created_by=self.user
        ).save()

    def test_get_unknown(self):
        response = self.client.get("/api/outages/v1/outages/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_known(self):
        response = self.client.get(f"/api/outages/v1/outages/{self.one.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {'scheduled': False,
                          'cancelled': False,
                          'title': "one",
                          'description': "Outage one",
                          'id': self.one.id,
                          'scheduled_start': None,
                          'scheduled_end': None,
                          'scheduled_severity': None,
                          'updates': []
                         })
        response = self.client.get(f"/api/outages/v1/outages/{self.two.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {'scheduled': False,
                          'cancelled': False,
                          'title': "two",
                          'description': "Outage two",
                          'id': self.two.id,
                          'scheduled_start': None,
                          'scheduled_end': None,
                          'scheduled_severity': None,
                          'updates': [{
                              'content': 'update one',
                              'severity': models.SEVERE,
                              'status': models.INVESTIGATING,
                              'time': datetime.isoformat(
                                  timezone.localtime(self.times[0]),
                                  timespec='auto')}]
                         })

    def test_get_known_redirect(self):
        response = self.client.get(f"/api/outages/v1/outages/{self.one.id}")
        self.assertEqual(response.status_code,
                         status.HTTP_301_MOVED_PERMANENTLY)
        self.assertEqual(response.headers["Location"],
                         f"/api/outages/v1/outages/{self.one.id}/")

    def test_get_all(self):
        response = self.client.get("/api/outages/v1/outages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0],
                         {'scheduled': False,
                          'cancelled': False,
                          'title': "one",
                          'description': "Outage one",
                          'id': self.one.id,
                          'scheduled_start': None,
                          'scheduled_end': None,
                          'scheduled_severity': None,
                          'updates': []
                         })

        self.assertEqual(data[1],
                         {'scheduled': False,
                          'cancelled': False,
                          'title': "two",
                          'description': "Outage two",
                          'id': self.two.id,
                          'scheduled_start': None,
                          'scheduled_end': None,
                          'scheduled_severity': None,
                          'updates': [{
                              'content': 'update one',
                              'severity': models.SEVERE,
                              'status': models.INVESTIGATING,
                              'time': datetime.isoformat(
                                  timezone.localtime(self.times[0]),
                                  timespec='auto')}]})
