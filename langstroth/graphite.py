from operator import itemgetter
import requests
from urllib.parse import urlencode

from django.conf import settings


GRAPHITE = settings.GRAPHITE_URL + "/render/"

# Addressing the history components
# within a 2-member data-point array.
VALUE_INDEX = 0
TIMESTAMP_INDEX = 1


def filter_null_datapoints(response_data):
    """Example Graphite response =
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
        data_series['datapoints'] = [datapoint
                                     for datapoint in data_points
                                     if datapoint[VALUE_INDEX] is not None]
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
    """Extend graphite data sets to the same length and fill in any missing
    values with either 0.0 or the previous real value that existed.

    """
    # Use the longest series as the template.  NVD3 requires that all
    # the datasets have the same data points.
    tmpl = sorted([(len(data['datapoints']), data['datapoints'])
                   for data in response_data],
                  key=itemgetter(0))[-1][1]
    tmpl = [[None, t] for v, t in tmpl]
    for data_series in response_data:
        data_points = data_series['datapoints']
        data_series['datapoints'] = list(_fill_nulls(data_points,
                                                     template=tmpl,
                                                     summarise=summarise))

    return response_data


class Target(object):

    def __init__(self, target):
        self._target = target

    def smartSummarize(self, step, aggregation='avg'):
        if step and aggregation:
            return self.__class__('smartSummarize(%s, "%s", "%s")'
                                  % (self._target, step, aggregation))
        return self

    def summarize(self, step, aggregation='avg'):
        if step and aggregation:
            return self.__class__('summarize(%s, "%s", "%s")'
                                  % (self._target, step, aggregation))
        return self

    def derivative(self):
        return self.__class__('derivative(%s)' % (self._target))

    def alias(self, name):
        return self.__class__('alias(%s, "%s")' % (self._target, name))

    def __str__(self):
        return self._target

    def __eq__(self, other):
        if type(other) is type(self):
            return self._target == other._target
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


def get(from_date=None, targets=[]):
    """Get some metrics from graphite.  Return a requests.models.Response
    object.

    """
    arguments = [('format', 'json')]
    arguments.extend([('target', str(target)) for target in targets])

    if from_date:
        arguments.append(('from', from_date))

    return requests.get(GRAPHITE + "?" + urlencode(arguments))
