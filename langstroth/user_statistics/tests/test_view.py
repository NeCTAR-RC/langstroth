import json
from unittest import mock

from django.test import TestCase


daily_accumulated_users = [
    {
        "name": "Cumulative",
        "points": [
            [1324216800000, 0.0],
            [1324303200000, 0.0],
            [1325512800000, 2.0],
            [1325599200000, 3.0],
        ],
    },
    {
        "name": "Frequency",
        "points": [
            [1324303200000, 0.0],
            [1325512800000, 2.0],
        ],
    },
]


class UserStatisticsViewTest(TestCase):
    # Web pages
    def test_user_registrations_page(self):
        response = self.client.get("/growth/users/")
        self.assertEqual(200, response.status_code)

    # Web services with JSON pay loads.
    @mock.patch('langstroth.metrics.user_statistics_series')
    def test_rest_for_frequency(self, mock_series):
        mock_series.return_value = daily_accumulated_users
        response = self.client.get(
            "/growth/users/rest/registrations/frequency"
        )
        assert 200 == response.status_code
        assert json.loads(response.content) == daily_accumulated_users
