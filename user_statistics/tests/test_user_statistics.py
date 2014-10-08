from django.test import TestCase
from pytest import fail

from requests import Response
import requests
from os import path

from user_statistics.services.user_statistics \
    import find_daily_accumulated_users
from user_statistics.tests.expected_users_statistics \
    import ExpectedUserStatistics


def path_for_tests(file_name):
    """Returns the absolute path to the merged dirname
    of the pathname and filename."""
    return path.abspath(path.join(path.dirname(__file__), file_name))


def dummy_get(url, **kwargs):
    if 'http://graphite.dev.rc.nectar.org.au/render' in url:
        file_path = path_for_tests(
            "./users_total_daily_graphite_response.json")
        with open(file_path) as user_json_file:
            user_json = user_json_file.read()
        response = Response()
        response.status_code = 200
        response._content = user_json
        return response

    fail("No response for URL: '%s'" % url)
    return Response()


class UserStatisticsTest(TestCase):

    def test_find_daily_accumulated_users_return_response(self):
        saved_get = requests.get
        requests.get = dummy_get
        try:
            actual_accumulated_users = \
                find_daily_accumulated_users()
            self.assertEqual(
                ExpectedUserStatistics
                .daily_accumulated_users,
                actual_accumulated_users)
        finally:
            requests.get = saved_get
