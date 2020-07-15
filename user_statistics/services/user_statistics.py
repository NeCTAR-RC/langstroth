from django.conf import settings
from langstroth import graphite


'''A user statistics service.

Including:
    a history of cumulative user registrations by day.

Daily accumulated user counts are obtained
by querying the Graphite service end-point.
'''


def find_daily_accumulated_users(from_date=None, until_date=None):
    '''Retrieve the history of the cumulative and frequency counts of users
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

    from_date = from_date or settings.USER_STATISTICS_START_DATE
    response = graphite.get(from_date=from_date,
                            until_date=until_date,
                            targets=targets)
    return graphite.filter_null_datapoints(response.json())
