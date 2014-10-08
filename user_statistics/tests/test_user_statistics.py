from django.test import TestCase
from pytest import fail

import datetime
from requests import Response
import requests
from os import path

from user_statistics.services.user_statistics \
    import UserStatistics
from user_statistics.tests.expected_users_statistics \
    import ExpectedUserStatistics


def path_for_tests(file_name):
    """Returns the absolute path to the merged dirname
    of the pathname and filename."""
    return path.abspath(path.join(path.dirname(__file__), file_name))


def totimestamp(dt, epoch=datetime.datetime(1970, 1, 1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds
            + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 1e6


def create_data_point(year, month, day, value):
    _data_point_date = datetime.datetime(year, month, day, 0, 0, 0)
    time_stamp = totimestamp(_data_point_date)
    datapoint = [value, time_stamp]
    return datapoint


@classmethod
def dummy_find_monthly_accumulated_users(cls):
    return ExpectedUserStatistics.daily_accumulated_users


def dummy_get(url, **kwargs):
    if 'http://graphite.dev.rc.nectar.org.au/render' in url:
        file_path = path_for_tests(
            "./users_total_daily_graphite_response.json")
        with open(file_path) as user_json_file:
            user_json = user_json_file.read()
        response = Response()
        response.status_code = 200
        response._content = user_json
        return response

    fail("No response for URL: '%s'" % url)
    return Response()


@classmethod
def dummy_find_daily_accumulated_users(cls):
    datapoint0 = create_data_point(2014, 10, 21, 5.0)
    datapoint1 = create_data_point(2014, 12, 28, 7.0)
    data = [datapoint0, datapoint1]
    return data


@classmethod
def dummy_date_range(cls, daily_accumulated_users):
    if not (2 == len(daily_accumulated_users)):
        fail("dummy_date_range::daily_accumulated_users FAILED")
    month0 = datetime.date(2014, 10, 1)
    month1 = datetime.date(2014, 11, 1)
    return month0, month1


@classmethod
def dummy_create_month_bins(cls, first_month, last_month):
    if not (datetime.date(2014, 10, 1) == first_month):
        fail("dummy_create_month_bins::first_month FAILED")
    if not (datetime.date(2014, 11, 1) == last_month):
        fail("dummy_create_month_bins::last_month FAILED")
    month0 = datetime.date(2014, 10, 1)
    month1 = datetime.date(2014, 11, 1)
    count = 0.0
    month_bins = {month0: count, month1: count}
    return month_bins


@classmethod
def dummy_populate_month_bins(cls, month_bins, daily_accumulated_users):
    if not (2 == len(month_bins)):
        fail("dummy_populate_month_bins month_bins FAILED")
    if not (2 == len(daily_accumulated_users)):
        fail("dummy_populate_month_bins daily_accumulated_users FAILED")
    month0 = datetime.date(2014, 10, 1)
    month1 = datetime.date(2014, 11, 1)
    month_bins[month0] = 5
    month_bins[month1] = 7


@classmethod
def dummy_monthly_bins_as_array(cls, month_bins):
    if not(2, len(month_bins)):
        fail("dummy_monthly_bins_as_array month_bins len FAILED")
    month0 = datetime.date(2014, 10, 1)
    month1 = datetime.date(2014, 11, 1)
    if not(5 == month_bins[month0]):
        fail("dummy_monthly_bins_as_array month_bins month0 FAILED")
    if not (7 == month_bins[month1]):
        fail("dummy_monthly_bins_as_array month_bins month1 FAILED")
    item0 = {'date': month0, 'count': 5}
    item1 = {'date': month1, 'count': 7}
    return [item0, item1]


@classmethod
def dummy_monthly_accumulated_users(cls):
    month0 = datetime.date(2014, 10, 1)
    month1 = datetime.date(2014, 11, 1)
    item0 = {'date': month0, 'count': 5}
    item1 = {'date': month1, 'count': 7}
    return [item0, item1]


class UserStatisticsTest(TestCase):

    def test_data_point_date(self):
        # In bash today: date +%s
        # 2014, 10, 17, 10, 46, 57
        datapoint = [0.0, 1413503217]
        actual_date = UserStatistics._data_point_date(datapoint)
        expected_date = datetime.date(2014, 10, 17)
        self.assertEqual(expected_date, actual_date)

    def test_data_point_month(self):
        # In bash today: date +%s
        # 2014, 10, 17
        datapoint = [0.0, 1413503217]
        actual_date = UserStatistics._data_point_month(datapoint)
        expected_date = datetime.date(2014, 10, 1)
        self.assertEqual(expected_date, actual_date)

    def test_data_point_last_month(self):
        # In bash today: date +%s
        # 2014, 10, 17
        datapoint = [0.0, 1413503217]
        actual_date = UserStatistics._data_point_last_month(datapoint)
        expected_date = datetime.date(2014, 9, 1)
        self.assertEqual(expected_date, actual_date)

    def test_create_month_bins_for_two_months(self):
        first_month = datetime.date(2014, 10, 1)
        last_month = datetime.date(2014, 11, 1)
        month_bins = UserStatistics._create_month_bins(first_month, last_month)
        self.assertEqual(2, len(month_bins))
        self.assertEqual(0.0, month_bins[first_month])
        self.assertEqual(0.0, month_bins[last_month])

    def test_create_month_bins_for_three_months(self):
        first_month = datetime.date(2014, 10, 1)
        middle_month = datetime.date(2014, 11, 1)
        last_month = datetime.date(2014, 12, 1)
        bins = UserStatistics._create_month_bins(first_month, last_month)
        self.assertEqual(3, len(bins))
        self.assertEqual(0.0, bins[first_month])
        self.assertEqual(0.0, bins[middle_month])
        self.assertEqual(0.0, bins[last_month])

    def test_populate_month_bins_for_one_month_one_data_point(self):
        month = datetime.date(2014, 10, 1)
        count = 0.0
        month_bins = {month: count}
        datapoint = create_data_point(2014, 10, 21, 5.0)
        data = [datapoint]
        UserStatistics._populate_month_bins(month_bins, data)
        self.assertEqual(1, len(month_bins))
        self.assertEqual(5, month_bins[month])

    def test_populate_month_bins_for_one_month_two_data_points(self):
        month = datetime.date(2014, 10, 1)
        count = 0.0
        month_bins = {month: count}
        datapoint0 = create_data_point(2014, 10, 21, 5.0)
        datapoint1 = create_data_point(2014, 10, 28, 7.0)
        data = [datapoint0, datapoint1]
        UserStatistics._populate_month_bins(month_bins, data)
        self.assertEqual(1, len(month_bins))
        self.assertEqual(7, month_bins[month])

    def test_populate_month_bins_for_two_months_two_data_points(self):
        month0 = datetime.date(2014, 10, 1)
        month1 = datetime.date(2014, 11, 1)
        count = 0.0
        month_bins = {month0: count, month1: count}
        datapoint0 = create_data_point(2014, 10, 21, 5.0)
        datapoint1 = create_data_point(2014, 11, 28, 7.0)
        data = [datapoint0, datapoint1]
        UserStatistics._populate_month_bins(month_bins, data)
        self.assertEqual(2, len(month_bins))
        self.assertEqual(5, month_bins[month0])
        self.assertEqual(7, month_bins[month1])

    def test_monthly_bins_as_array(self):
        month0 = datetime.date(2014, 10, 1)
        month1 = datetime.date(2014, 11, 1)
        month_bins = {month0: 7, month1: 8}
        bins_array = UserStatistics._monthly_bins_as_array(month_bins)
        self.assertEqual(2, len(bins_array))
        self.assertEqual(month0, bins_array[0]['date'])
        self.assertEqual(month1, bins_array[1]['date'])
        self.assertTrue(month1 > month0)
        self.assertEqual(7, bins_array[0]['count'])
        self.assertEqual(8, bins_array[1]['count'])

    def test_monthly_accumulated_users_calls(self):
        saved_find_daily_accumulated_users = \
            UserStatistics._find_daily_accumulated_users
        saved_date_range = UserStatistics._date_range
        saved_create_month_bins = UserStatistics._create_month_bins
        saved_populate_month_bins = UserStatistics._populate_month_bins
        saved_monthly_bins_as_array = UserStatistics._monthly_bins_as_array
        UserStatistics._find_daily_accumulated_users = \
            dummy_find_daily_accumulated_users
        UserStatistics._date_range = dummy_date_range
        UserStatistics._create_month_bins = dummy_create_month_bins
        UserStatistics._populate_month_bins = dummy_populate_month_bins
        UserStatistics._monthly_bins_as_array = dummy_monthly_bins_as_array
        try:
            actual_result = UserStatistics._monthly_accumulated_users()
            month0 = datetime.date(2014, 10, 1)
            month1 = datetime.date(2014, 11, 1)
            item0 = {'date': month0, 'count': 5}
            item1 = {'date': month1, 'count': 7}
            expected_result = [item0, item1]
            self.assertEqual(expected_result, actual_result)
        finally:
            UserStatistics._find_daily_accumulated_users = \
                saved_find_daily_accumulated_users
            UserStatistics._date_range = saved_date_range
            UserStatistics._create_month_bins = saved_create_month_bins
            UserStatistics._populate_month_bins = saved_populate_month_bins
            UserStatistics._monthly_bins_as_array = saved_monthly_bins_as_array

    def test_monthly_frequency(self):
        saved_monthly_accumulated_users = \
            UserStatistics._monthly_accumulated_users
        UserStatistics._monthly_accumulated_users = \
            dummy_monthly_accumulated_users
        try:
            month0 = datetime.date(2014, 10, 1)
            month1 = datetime.date(2014, 11, 1)
            item0 = {'date': month0, 'count': 5}
            item1 = {'date': month1, 'count': 2}
            expected_frequency = [item0, item1]
            actual_frequency = UserStatistics.monthly_frequency()
            self.assertEqual(
                expected_frequency,
                actual_frequency)
        finally:
            UserStatistics._monthly_accumulated_users = \
                saved_monthly_accumulated_users

    def test_find_daily_accumulated_users_return_response(self):
        saved_get = requests.get
        requests.get = dummy_get
        try:
            actual_accumulated_users = \
                UserStatistics._find_daily_accumulated_users()
            self.assertEqual(
                ExpectedUserStatistics
                .daily_accumulated_users,
                actual_accumulated_users)
        finally:
            requests.get = saved_get

    def test_monthly_accumulated_users_returns_correct_dates(self):
        saved_get = requests.get
        requests.get = dummy_get
        try:
            actual_accumulated_users = \
                UserStatistics._monthly_accumulated_users()
            actual_dates = map(
                lambda item: item['date'], actual_accumulated_users)
            self.assertEqual(
                ExpectedUserStatistics.start_month_dates,
                actual_dates)
        finally:
            requests.get = saved_get
