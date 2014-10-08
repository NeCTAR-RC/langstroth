from django.test import TestCase

from requests import Response
import requests
import json


class UserStatisticsViewTest(TestCase):

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

    @staticmethod
    def dummy_get(url, **kwargs):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(
            UserStatisticsViewTest.daily_accumulated_users)
        return response

    # Web pages

    def test_page_index(self):
        response = self.client.get(
            "/user_statistics/")
        self.assertEqual(200, response.status_code)

    def test_page_visualisation(self):
        response = self.client.get(
            "/user_statistics/registrations/visualisation")
        self.assertEqual(200, response.status_code)

    # Web services with JSON pay loads.

    def test_rest_for_frequency(self):

        saved_get = requests.get
        requests.get = self.dummy_get
        try:
            response = self.client.get(
                "/user_statistics/rest/registrations/frequency")
            self.assertEqual(200, response.status_code)
        finally:
            requests.get = saved_get
