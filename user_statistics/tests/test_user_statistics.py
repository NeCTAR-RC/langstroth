from os import path

import httpretty

from user_statistics.services.user_statistics \
    import find_daily_accumulated_users


def path_for_tests(file_name):
    """Returns the absolute path to the merged dirname
    of the pathname and filename."""
    return path.abspath(path.join(path.dirname(__file__), file_name))

FILE_PATH = path_for_tests("./users_total_daily_graphite_response.json")


@httpretty.activate
def test_find_daily_accumulated_users():
    httpretty.register_uri(
        httpretty.GET,
        'http://graphite.dev.rc.nectar.org.au/render/',
        body=open(FILE_PATH).read(),
        content_type="application/json")

    expected_daily_accumulated_users = [
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

    actual_accumulated_users = find_daily_accumulated_users()
    assert expected_daily_accumulated_users == actual_accumulated_users
