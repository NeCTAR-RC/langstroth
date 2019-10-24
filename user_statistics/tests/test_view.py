import json
from unittest import mock

from django.test import TestCase


daily_accumulated_users = [
    {
        "target": "Cumulative",
        "datapoints": [
            [0.0, 1324216800],
            [0.0, 1324303200],
            [2.0, 1325512800],
            [3.0, 1325599200],
        ]
    },
    {
        "target": "Frequency",
        "datapoints": [
            [0.0, 1324303200],
            [2.0, 1325512800],
        ]
    }
]


class UserStatisticsViewTest(TestCase):

    # Web pages
    def test_user_registrations_page(self):
        response = self.client.get(
            "/growth/users/")
        self.assertEqual(200, response.status_code)

    # Web services with JSON pay loads.
    @mock.patch('langstroth.graphite.requests.get')
    def test_rest_for_frequency(self, mock_get):
        mock_get.return_value.json.return_value = daily_accumulated_users
        response = self.client.get(
            "/growth/users/rest/registrations/frequency")
        assert 200 == response.status_code
        assert json.loads(response.content) == daily_accumulated_users
