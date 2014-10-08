import requests
from django.conf import settings
from urllib import urlencode
import json
from langstroth.graphite import filter_null_datapoints


'''
A user statistics service.

Including:
    a history of cumulative user registrations by day.

Daily accumulated user counts are obtained
by querying the Graphite service end-point.
'''

'''
The Graphite query string needs to be url encoded.
# E.g. ?target=summarize(users.total,"1day","max")
# &format=json&from=20111201
# becomes:
# ?target=summarize(users.total%2C%227d%22%2C%22max%22)
# &format=json&from=20110801
'''

__GRAPHITE_API_URL = settings.GRAPHITE_URL + '/render'

__FORMAT = 'json'

__BASE_ARGUMENTS = [
    ('format', __FORMAT),
    ('from', settings.USER_STATISTICS_START_DATE),
]


def _data_series_order(response_data):
    if response_data[0]['target'] == "Cumulative":
        cumulative_index = 0
        frequency_index = 1
    else:
        cumulative_index = 1
        frequency_index = 0
    return cumulative_index, frequency_index


def find_daily_accumulated_users():
    '''
    Retrieve the history of the cumulative and frequency counts of users
    added by the end of each day.
    '''
    cumulative_users_at_end_of_day = \
        'alias(smartSummarize(users.total,"1d","max", True),' \
        '"Cumulative")'
    frequency_users_at_end_of_day = \
        'alias(derivative(summarize(users.total,"1d","max", True)),' \
        '"Frequency")'
    graphite_targets = [cumulative_users_at_end_of_day,
                        frequency_users_at_end_of_day]
    response_data = _query_graphite_api(graphite_targets)
    return filter_null_datapoints(response_data)


def _query_graphite_api(graphite_targets):
    '''
    Issue a HTTP request to the Graphite end-point
    and return just the data points as a list.
    '''
    arguments = __BASE_ARGUMENTS + \
        [('target', target) for target in graphite_targets]
    query = '?' + urlencode(arguments)
    response = requests.get(__GRAPHITE_API_URL + query)
    body_str = response.content
    return json.loads(body_str)
