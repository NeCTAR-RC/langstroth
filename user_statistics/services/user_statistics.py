from django.conf import settings
from langstroth import graphite


'''
A user statistics service.

Including:
    a history of cumulative user registrations by day.

Daily accumulated user counts are obtained
by querying the Graphite service end-point.
'''


def find_daily_accumulated_users():
    '''
    Retrieve the history of the cumulative and frequency counts of users
    added by the end of each day.
    '''
    targets = []

    targets.append(graphite.Target('users.total')
                   .smartSummarize('1d', 'max')
                   .alias('Cumulative'))
    targets.append(graphite.Target('users.total')
                   .smartSummarize('1d', 'max')
                   .derivative()
                   .alias('Frequency'))

    response = graphite.get(from_date=settings.USER_STATISTICS_START_DATE,
                            targets=targets)
    return graphite.filter_null_datapoints(response.json())
