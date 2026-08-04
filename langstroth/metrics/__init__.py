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
the front-end charts consume ([{"target": <series name>,
"datapoints": [[value|None, timestamp], ...]}], timestamps in unix
seconds); composition_values returns [{"target": <group>, "value":
<total>}, ...] sorted ascending by value. The filter/fill helpers
below post-process the datapoint structure and are backend
independent.
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
# within a 2-member data-point array.
VALUE_INDEX = 0
TIMESTAMP_INDEX = 1


def filter_null_datapoints(response_data):
    """Example response =
    [
        {
            "target": "Cumulative",
            "datapoints": [
                [null, 1324130400],
                [0.0, 1324216800],
                [null, 1413208800]
            ]
        },
    ]

    Remove any datapoint with a null value component.
    """

    for data_series in response_data:
        data_points = data_series['datapoints']
        data_series['datapoints'] = [
            datapoint
            for datapoint in data_points
            if datapoint[VALUE_INDEX] is not None
        ]
    return response_data


def _fill_nulls(data, template, summarise=None):
    data = dict([(timestamp, value) for value, timestamp in data])
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
            yield [previous_value, timestamp]
        else:
            previous_value = value
            yield [value, timestamp]


def fill_null_datapoints(response_data, summarise=None):
    """Extend the data sets to the same length and fill in any missing
    values with either 0.0 or the previous real value that existed.

    """
    if not response_data:
        return response_data
    # Use the longest series as the template.  NVD3 requires that all
    # the datasets have the same data points.
    tmpl = sorted(
        [
            (len(data['datapoints']), data['datapoints'])
            for data in response_data
        ],
        key=itemgetter(0),
    )[-1][1]
    tmpl = [[None, t] for v, t in tmpl]
    for data_series in response_data:
        data_points = data_series['datapoints']
        data_series['datapoints'] = list(
            _fill_nulls(data_points, template=tmpl, summarise=summarise)
        )

    return response_data
