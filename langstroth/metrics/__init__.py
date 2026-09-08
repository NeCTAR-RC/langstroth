"""Pluggable time-series backends for the growth, composition and
user statistics pages.

The METRICS_BACKEND setting selects the active backend: either a
short name registered in BACKENDS or a dotted module path, so adding
a backend is one module plus a settings change.

A backend module must provide three functions:

- aggregate_series(metric, series, from_date=None, until_date=None,
  summarise=None, now=None)
- composition_values(name, azs, now=None)
- user_statistics_series(from_date, until_date=None, now=None)

aggregate_series and user_statistics_series return the JSON structure
the front-end charts consume ([{"name": <series name>, "points":
[[timestamp_ms, value|None], ...]}], timestamps in unix
milliseconds); composition_values returns [{"name": <group>, "value":
<total>}, ...] sorted ascending by value. The filter/fill helpers
below post-process the point structure and are backend independent.
"""

from importlib import import_module
from operator import itemgetter

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

BACKENDS = {
    'victoriametrics': 'langstroth.metrics.victoriametrics',
}


def get_backend():
    """Import the module named by METRICS_BACKEND (a BACKENDS short
    name or a dotted module path)."""
    name = settings.METRICS_BACKEND
    try:
        return import_module(BACKENDS.get(name, name))
    except ImportError as ex:
        raise ImproperlyConfigured(
            f"METRICS_BACKEND {name!r} could not be imported: {ex}"
        )


def aggregate_series(*args, **kwargs):
    return get_backend().aggregate_series(*args, **kwargs)


def composition_values(*args, **kwargs):
    return get_backend().composition_values(*args, **kwargs)


def user_statistics_series(*args, **kwargs):
    return get_backend().user_statistics_series(*args, **kwargs)


# Addressing the history components
# within a 2-member point array.
TIMESTAMP_INDEX = 0
VALUE_INDEX = 1


def filter_null_points(response_data):
    """Example response =
    [
        {
            "name": "Cumulative",
            "points": [
                [1324130400000, null],
                [1324216800000, 0.0],
                [1413208800000, null]
            ]
        },
    ]

    Remove any point with a null value component.
    """

    for data_series in response_data:
        points = data_series['points']
        data_series['points'] = [
            point for point in points if point[VALUE_INDEX] is not None
        ]
    return response_data


def _fill_nulls(data, template, summarise=None):
    data = dict([(timestamp, value) for timestamp, value in data])
    previous_value = 0.0
    no_data_count = 0
    if summarise == '3days':
        max_no_data = 2
    elif summarise == '1days':
        max_no_data = 6
    elif summarise == '12hours':
        max_no_data = 12
    else:
        max_no_data = 30

    for point in template:
        timestamp = point[TIMESTAMP_INDEX]
        value = point[VALUE_INDEX]
        if timestamp in data:
            value = data[timestamp]
        if value is None:
            if no_data_count > max_no_data:
                previous_value = 0.0
            no_data_count += 1
            yield [timestamp, previous_value]
        else:
            previous_value = value
            yield [timestamp, value]


def fill_null_points(response_data, summarise=None):
    """Extend the data sets to the same length and fill in any missing
    values with either 0.0 or the previous real value that existed.

    Stacked charts need every series defined at every x position, so
    all series are gridded onto the longest series' timestamps.
    """
    if not response_data:
        return response_data
    tmpl = sorted(
        [(len(data['points']), data['points']) for data in response_data],
        key=itemgetter(0),
    )[-1][1]
    tmpl = [[t, None] for t, v in tmpl]
    for data_series in response_data:
        points = data_series['points']
        data_series['points'] = list(
            _fill_nulls(points, template=tmpl, summarise=summarise)
        )

    return response_data
