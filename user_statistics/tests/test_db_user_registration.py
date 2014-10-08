from django.test import TestCase

from datetime import date

from user_statistics.models.registration import UserRegistration


class UserRegistrationDBTest(TestCase):

    multi_db = True

    def setUp(self):
        UserRegistration.objects.create(
            user_name="1234", creation_time="2014-02-16T23:21:59Z")
        UserRegistration.objects.create(
            user_name="4321", creation_time="2014-02-22T16:14:30Z")

    def test_code_has_name(self):
        barrym = UserRegistration.objects.get(user_name="1234")
        phyllisu = UserRegistration.objects.get(user_name="4321")
        self.assertEqual(
            '2014-02-16 23:21:59',
            barrym.creation_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(
            '2014-02-22 16:14:30',
            phyllisu.creation_time.strftime('%Y-%m-%d %H:%M:%S'))

    def test_dict(self):
        expected_map = {
            '1234': '2014-02-16 23:21:59',
            '4321': '2014-02-22 16:14:30'}
        actual_map = UserRegistration.user_dict()
        different_items = set(expected_map.items()) ^ set(actual_map.items())
        self.assertEqual(0, len(different_items))

    def test_history(self):
        expected_list = [
            {'user_name': '1234', 'creation_time': '2014-02-16 23:21:59'},
            {'user_name': '4321', 'creation_time': '2014-02-22 16:14:30'}
        ]
        actual_list = UserRegistration.history()
        self.assertEqual(2, len(actual_list))
        self.assertEqual(expected_list, actual_list)

    def test_frequency_2_items_in_2_separate_bins(self):
        expected_list = [
            {'date': date(2014, 02, 16), 'count': 1},
            {'date': date(2014, 02, 17), 'count': 0},
            {'date': date(2014, 02, 18), 'count': 0},
            {'date': date(2014, 02, 19), 'count': 0},
            {'date': date(2014, 02, 20), 'count': 0},
            {'date': date(2014, 02, 21), 'count': 0},
            {'date': date(2014, 02, 22), 'count': 1}
        ]
        actual_list = UserRegistration.frequency()
        # The code now fills in empty bins over the entire date range
        # on a daily basis.
        self.assertEqual(7, len(actual_list))
        self.assertEqual(expected_list, actual_list)

    def test_frequency_4_items_in_2_separate_bins(self):
        UserRegistration.objects.create(
            user_name="aaaa", creation_time="2014-02-16T05:07:00Z")
        UserRegistration.objects.create(
            user_name="4bbbb", creation_time="2014-02-22T00:59:45Z")
        expected_list = [
            {'date': date(2014, 02, 16), 'count': 2},
            {'date': date(2014, 02, 17), 'count': 0},
            {'date': date(2014, 02, 18), 'count': 0},
            {'date': date(2014, 02, 19), 'count': 0},
            {'date': date(2014, 02, 20), 'count': 0},
            {'date': date(2014, 02, 21), 'count': 0},
            {'date': date(2014, 02, 22), 'count': 2}
        ]
        actual_list = UserRegistration.frequency()
        # The code now fills in empty bins over the entire date range
        # on a daily basis.
        self.assertEqual(7, len(actual_list))
        self.assertEqual(expected_list, actual_list)
