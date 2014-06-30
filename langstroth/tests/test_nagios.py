import os

from django.test import TestCase

from langstroth import nagios

DIR = os.path.abspath(os.path.dirname(__file__))


class TestAvailability(TestCase):
    maxDiff = None

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
                          {'name': 'Designate',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '100.000%',
                           'critical': '0.000%'},
                          {'name': 'Glance (Registry)',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.897%',
                           'critical': '0.103%'},
                          {'name': 'Glance',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '99.982%',
                           'critical': '0.018%'},
                          {'name': 'Heat',
                           'unknown': '0.000%',
                           'warning': '0.000%',
                           'ok': '100.000%',
                           'critical': '0.000%'},
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


class TestStatus(TestCase):
    maxDiff = None

    def test_parsing(self):
        html = open(os.path.join(DIR, 'test_status.html')).read()
        result = nagios.parse_status(html)
        self.assertEqual(
            result,
            {'hosts':
             {'cinder.rc.nectar.org.au':
              {'hostname': 'cinder.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 25m 54s',
                             'last_checked': '2014-06-30 10:48:23',
                             'name': 'http_cinder-api',
                             'status': 'OK'}]},
              'dashboard.rc.nectar.org.au':
              {'hostname': 'dashboard.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 25m 33s',
                             'last_checked': '2014-06-30 10:48:50',
                             'name': 'https',
                             'status': 'OK'}]},
              'designate.rc.nectar.org.au':
              {'hostname': 'designate.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h 49m 41s',
                             'last_checked': '2014-06-30 10:51:52',
                             'name': 'http_designate-api',
                             'status': 'OK'}]},
              'glance-registry.rc.nectar.org.au':
              {'hostname': 'glance-registry.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 27m 41s',
                             'last_checked': '2014-06-30 10:48:50',
                             'name': 'http_glance-registry',
                             'status': 'OK'}]},
              'glance.rc.nectar.org.au':
              {'hostname': 'glance.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h  1m 18s',
                             'last_checked': '2014-06-30 10:49:12',
                             'name': 'http_glance-api',
                             'status': 'OK'}]},
              'heat.rc.nectar.org.au':
              {'hostname': 'heat.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h 53m 55s',
                             'last_checked': '2014-06-30 10:49:33',
                             'name': 'http_heat-api',
                             'status': 'OK'}]},
              'keystone.rc.nectar.org.au':
              {'hostname': 'keystone.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 25m 32s',
                             'last_checked': '2014-06-30 10:48:02',
                             'name': 'http_keystone-adm',
                             'status': 'OK'},
                            {'duration': ' 6d 23h 25m 11s',
                             'last_checked': '2014-06-30 10:48:24',
                             'name': 'http_keystone-pub',
                             'status': 'OK'}]},
              'nova.rc.nectar.org.au':
              {'hostname': 'nova.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 26m 58s',
                             'last_checked': '2014-06-30 10:50:44',
                             'name': 'http_ec2',
                             'status': 'OK'},
                            {'duration': ' 6d 23h 26m 37s',
                             'last_checked': '2014-06-30 10:51:07',
                             'name': 'http_nova-api',
                             'status': 'OK'}]}}})
