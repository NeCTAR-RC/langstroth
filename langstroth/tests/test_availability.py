import os

from django.test import TestCase

from langstroth import nagios

DIR = os.path.abspath(os.path.dirname(__file__))


class TestAvailability(TestCase):
    def test_parsing(self):
        html = open(os.path.join(DIR, 'test_availability.html')).read()
        result = nagios.parse_availability(html)
        self.assertEqual(
            result,
            {'report_range': '2013-12-26 20:26:19 to 2014-06-26 09:27:51',
             'services': [{'name': 'Cinder',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.945%',
                           'critical': '0.055%'},
                          {'name': 'Dashboard',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.795%',
                           'critical': '0.205%'},
                          {'name': 'Glance',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.897%',
                           'critical': '0.103%'},
                          {'name': 'Keystone (Admin)',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.926%',
                           'critical': '0.074%'},
                          {'name': 'Keystone',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.901%',
                           'critical': '0.099%'},
                          {'name': 'Nova (EC2)',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.587%',
                           'critical': '0.413%'},
                          {'name': 'Nova',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.567%',
                           'critical': '0.433%'}],
             'average': {'unknown': '0.000%',
                         'warning': '0.000%',
                         'ok': '99.860%',
                         'name': 'Average',
                         'critical': '0.140%'}})
