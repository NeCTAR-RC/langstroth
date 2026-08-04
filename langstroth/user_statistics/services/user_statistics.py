import logging

from django.conf import settings
import requests

from langstroth import metrics


'''A user statistics service.

Including:
    a history of cumulative user registrations by day.

Daily accumulated user counts are obtained from the configured
metrics backend.
'''

LOG = logging.getLogger(__name__)


def find_daily_accumulated_users(from_date=None, until_date=None):
    '''Retrieve the history of the cumulative and frequency counts of users
    added by the end of each day.

    Returns an empty list if the metrics backend is unavailable.
    '''
    from_date = from_date or settings.USER_STATISTICS_START_DATE
    try:
        data = metrics.user_statistics_series(from_date, until_date)
        return metrics.filter_null_datapoints(data)
    except (requests.RequestException, ValueError) as ex:
        LOG.warning(
            "Problem fetching user statistics from the metrics backend",
            exc_info=ex,
        )
        return []
