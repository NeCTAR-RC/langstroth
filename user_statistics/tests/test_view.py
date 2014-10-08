from django.test import TestCase


class UserStatisticsViewTest(TestCase):

    fixtures = ['user_statistics_0']
    multi_db = True

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

    def test_rest_for_history(self):
        response = self.client.get(
            "/user_statistics/rest/registrations/history")
        self.assertEqual(200, response.status_code)

    def test_rest_for_frequency(self):
        response = self.client.get(
            "/user_statistics/rest/registrations/frequency")
        self.assertEqual(200, response.status_code)
