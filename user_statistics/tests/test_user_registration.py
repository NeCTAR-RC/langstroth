from django.utils import unittest
from datetime import date

from user_statistics.models.registration import UserRegistration


class UserRegistrationTest(unittest.TestCase):

    barrym = None
    phyllisu = None

    def setUp(self):
        self.barrym = UserRegistration(
            user_name="1234", creation_time="2014-02-16")
        self.phyllisu = UserRegistration(
            user_name="4321", creation_time="2014-03-08")

    def tearDown(self):
        self.barrym = None
        self.phyllisu = None

    def test_UserRegistration_has_user_name(self):

        self.assertEqual(self.barrym.user_name, '1234')
        self.assertEqual(self.phyllisu.user_name, '4321')

    def test_UserRegistration_has_creation_time(self):
        self.assertEqual(self.barrym.creation_time, '2014-02-16')
        self.assertEqual(self.phyllisu.creation_time, '2014-03-08')

    def test_UserRegistration_monthly_frequency_with_one_day(self):
        date0 = date(2014, 02, 16)
        last_month_date0 = date(2014, 03, 26)
        item0 = {'date': date0, 'count': 1}
        item1 = {'date': last_month_date0, 'count': 0}
        items = [item0, item1]
        UserRegistration.frequency = staticmethod(lambda: items)
        frequency = UserRegistration.monthly_frequency()
        self.assertEqual(1, len(frequency))
        actual_item = frequency[0]
        self.assertEqual(date(2014, 2, 1), actual_item['date'])
        self.assertEqual(1, actual_item['count'])

    def test_UserRegistration_monthly_frequency_with_two_days_same_month(self):
        date0 = date(2014, 02, 16)
        date1 = date(2014, 02, 26)
        last_month_date0 = date(2014, 03, 26)
        item0 = {'date': date0, 'count': 1}
        item1 = {'date': date1, 'count': 2}
        item2 = {'date': last_month_date0, 'count': 0}
        items = [item0, item1, item2]
        UserRegistration.frequency = staticmethod(lambda: items)
        frequency = UserRegistration.monthly_frequency()
        self.assertEqual(1, len(frequency))
        actual_item0 = frequency[0]
        self.assertEqual(date(2014, 02, 1), actual_item0['date'])
        self.assertEqual(3, actual_item0['count'])

    def test_UserRegistration_monthly_frequency_with_two_days_adjacent_months(self):  # noqa
        date0 = date(2014, 02, 16)
        date1 = date(2014, 03, 26)
        last_month_date0 = date(2014, 04, 26)
        item0 = {'date': date0, 'count': 5}
        item1 = {'date': date1, 'count': 0}
        item2 = {'date': last_month_date0, 'count': 0}
        items = [item0, item1, item2]
        UserRegistration.frequency = staticmethod(lambda: items)
        frequency = UserRegistration.monthly_frequency()
        self.assertEqual(2, len(frequency))
        actual_item0 = frequency[0]
        self.assertEqual(date(2014, 02, 1), actual_item0['date'])
        self.assertEqual(5, actual_item0['count'])
        actual_item1 = frequency[1]
        self.assertEqual(date(2014, 3, 1), actual_item1['date'])
        self.assertEqual(0, actual_item1['count'])

    def test_UserRegistration_monthly_frequency_with_incomplete_last_month(self):  # noqa
        previous_month_date0 = date(2014, 9, 27)
        previous_month_date1 = date(2014, 9, 28)
        previous_month_date2 = date(2014, 9, 29)
        previous_month_date3 = date(2014, 9, 30)
        last_month_date0 = date(2014, 10, 26)
        item0 = {'date': previous_month_date0, 'count': 50}
        item1 = {'date': previous_month_date1, 'count': 40}
        item2 = {'date': previous_month_date2, 'count': 30}
        item3 = {'date': previous_month_date3, 'count': 20}
        item4 = {'date': last_month_date0, 'count': 10}
        items = [item0, item1, item2, item3, item4]
        UserRegistration.frequency = staticmethod(lambda: items)
        frequency = UserRegistration.monthly_frequency()
        self.assertEqual(1, len(frequency))
        actual_item0 = frequency[0]
        self.assertEqual(date(2014, 9, 1), actual_item0['date'])
        self.assertEqual(140, actual_item0['count'])

    def test_UserRegistration_mid_month(self):
        date0 = date(2014, 02, 16)
        mid_month_date = UserRegistration.mid_month(date0)
        self.assertEqual(date(2014, 2, 14), mid_month_date)

    def test_UserRegistration_last_date_of_month(self):
        date0 = date(2014, 02, 16)
        last_month_date = UserRegistration.last_date_of_month(date0)
        self.assertEqual(date(2014, 2, 28), last_month_date)
