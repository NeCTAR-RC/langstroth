from unittest import mock

from langstroth.user_statistics.services import user_statistics


GRAPHITE_OUTPUT = [
    {"target": "Cumulative",
     "datapoints": [
         [None, 1324130400],
         [0.0, 1324216800],
         [0.0, 1324303200],
         [2.0, 1325512800],
         [3.0, 1325599200],
         [None, 1413208800]
     ]
    },
    {
        "target": "Frequency",
        "datapoints": [
            [None, 1324130400],
            [None, 1324216800],
            [0.0, 1324303200],
            [2.0, 1325512800],
            [None, 1325599200],
            [None, 1413208800]
        ]
    }
]


@mock.patch('langstroth.graphite.requests.get')
def test_find_daily_accumulated_users(mock_get):
    mock_get.return_value.json.return_value = GRAPHITE_OUTPUT

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

    actual_accumulated_users = user_statistics.find_daily_accumulated_users()
    assert expected_daily_accumulated_users == actual_accumulated_users
