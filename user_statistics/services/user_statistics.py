import requests
import logging
from django.conf import settings
from urllib import urlencode
import json
import datetime
from datetime import timedelta
from operator import itemgetter

LOG = logging.getLogger(__name__)


class UserStatistics(object):

    '''
    A user statistics service.

    Including:
        a history of cumulative user registrations
    Proper month binning is supported.

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

    # Addressing the history components
    # within a 2-member data-point array.
    __COUNT_INDEX = 0
    __DATE_INDEX = 1

    @classmethod
    def _data_point_date(cls, datapoint):
        return datetime.date.fromtimestamp(datapoint[cls.__DATE_INDEX])

    @classmethod
    def _data_point_month(cls, datapoint):
        '''
        Return a month as signified by
        the date of the first day of the month.
        '''
        return datetime.date.fromtimestamp(
            datapoint[cls.__DATE_INDEX]).replace(day=1)

    @classmethod
    def _data_point_last_month(cls, last_datapoint):
        '''
        The statistics for the last month is always incomplete,
        so instead we return the previous month which will be complete.
        '''
        last_month = cls._data_point_month(last_datapoint)
        last_month = (last_month - timedelta(days=1)).replace(day=1)
        return last_month

    @staticmethod
    def last_date_of_month(date):
        return (date + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    @classmethod
    def _date_range(cls, daily_accumulated_users):
        '''
        From the user history
        calculate the inclusive data range
        on a whole month basis.
        Ignore the incomplete statistics of the last month.
        '''
        first = daily_accumulated_users[0]
        last = daily_accumulated_users[len(daily_accumulated_users) - 1]
        first_month = cls._data_point_month(first)
        last_month = cls._data_point_last_month(last)
        return first_month, last_month

    @classmethod
    def _create_month_bins(cls, first_month, last_month):
        '''
        Build bins as a map.
        '''
        month_bins = dict()
        date = first_month
        while date <= last_month:
            month_bins[date] = 0
            date = (date + timedelta(days=31)).replace(day=1)
        return month_bins

    @classmethod
    def _populate_month_bins(cls, known_months, daily_accumulated_users):
        '''
        Populate month bins
        '''
        for current_total in daily_accumulated_users:
            day_date = cls._data_point_date(current_total)
            day_count = current_total[cls.__COUNT_INDEX]
            month = datetime.date(day_date.year, day_date.month, 1)
            if month in known_months:
                known_months[month] = max(int(day_count), known_months[month])

    @classmethod
    def _monthly_bins_as_array(cls, month_bins):
        '''
        Reorganise monthly bins into a date sorted array of
        dictionary items.
        '''
        monthly_registrations = []
        for month in month_bins:
            item = {'date': month, 'count': month_bins[month]}
            monthly_registrations.append(item)

        monthly_registrations = sorted(
            monthly_registrations, key=itemgetter('date'))
        return monthly_registrations

    @classmethod
    def monthly_frequency(cls):
        accumulated_users = cls._monthly_accumulated_users()
        previous = 0
        frequency = []
        for cumulative_statistic in accumulated_users:
            difference = cumulative_statistic['count'] - previous
            previous = cumulative_statistic['count']
            frequency_statistic = {
                'date': cumulative_statistic["date"],
                'count': difference}
            frequency.append(frequency_statistic)
        return frequency

    @classmethod
    def _monthly_accumulated_users(cls):
        '''
        Determine the history of the
        cumulative registered user count
        at the end of each month.

        The data from a Graphite API query by day is post processed,
        since the Graphite function summarize has a bin of
        1month = 30 days exactly,
        and so doesn't produce the desired result.
        '''
        daily_accumulated_users = cls._find_daily_accumulated_users()
        first_month, last_month = cls._date_range(daily_accumulated_users)
        month_bins = cls._create_month_bins(first_month, last_month)
        cls._populate_month_bins(month_bins, daily_accumulated_users)
        accumulated_registrations = cls._monthly_bins_as_array(month_bins)
        return accumulated_registrations

    @classmethod
    def _find_daily_accumulated_users(cls):
        '''
        Retrieve the history of the cumulative count of users
        added by the end of each day.
        '''
        accumulated_users_at_end_of_month = \
            'summarize(users.total,"1d","max", True)'
        return cls._query_graphite_api(accumulated_users_at_end_of_month)

    @classmethod
    def _query_graphite_api(cls, api_function):
        '''
        Issue a HTTP request to the Graphite end-point
        and return just the data points as a list.
        '''
        argments = cls.__BASE_ARGUMENTS + \
            [('target', api_function)]
        query = '?' + urlencode(argments)
        response = requests.get(cls.__GRAPHITE_API_URL + query)
        body_str = response.content
        data = json.loads(body_str)[0]['datapoints']
        return filter(lambda item: item[0] is not None, data)
