from django import test
from django.urls import reverse

from langstroth import models as auth_models
from langstroth.outages import models


class ViewTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com",
            is_superuser=True)
        cls.outage1 = models.Outage.objects.create(
            scheduled=True, title="one", description="Outage one",
            created_by=cls.user)
        cls.outage2 = models.Outage.objects.create(
            scheduled=False, title="one", description="Outage one",
            created_by=cls.user)

    def test_list(self):
        response = self.client.get(reverse('outages:list'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        outage = models.Outage.objects.get(pk=1)
        response = self.client.get(outage.get_absolute_url())
        self.assertEqual(response.status_code, 200)
