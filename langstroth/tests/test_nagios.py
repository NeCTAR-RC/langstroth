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
            {'average': {'critical': '0.140%',
                         'name': 'Average',
                         'ok': '99.860%',
                         'unknown': '0.000%',
                         'warning': '0.000%'},
             'services': {
                 'http_cinder-api': {'critical': '0.055%',
                                     'name': 'http_cinder-api',
                                     'ok': '99.945%',
                                     'unknown': '0.000%',
                                     'warning': '0.000%'},
                 'http_designate-api': {'critical': '0.000%',
                                        'name': 'http_designate-api',
                                        'ok': '100.000%',
                                        'unknown': '0.000%',
                                        'warning': '0.000%'},
                 'http_ec2': {'critical': '0.413%',
                              'name': 'http_ec2',
                              'ok': '99.587%',
                              'unknown': '0.000%',
                              'warning': '0.000%'},
                 'http_glance-api': {'critical': '0.018%',
                                     'name': 'http_glance-api',
                                     'ok': '99.982%',
                                     'unknown': '0.000%',
                                     'warning': '0.000%'},
                 'http_glance-registry': {'critical': '0.103%',
                                          'name': 'http_glance-registry',
                                          'ok': '99.897%',
                                          'unknown': '0.000%',
                                          'warning': '0.000%'},
                 'http_heat-api': {'critical': '0.000%',
                                   'name': 'http_heat-api',
                                   'ok': '100.000%',
                                   'unknown': '0.000%',
                                   'warning': '0.000%'},
                 'http_keystone-adm': {'critical': '0.074%',
                                       'name': 'http_keystone-adm',
                                       'ok': '99.926%',
                                       'unknown': '0.000%',
                                       'warning': '0.000%'},
                 'http_keystone-pub': {'critical': '0.099%',
                                       'name': 'http_keystone-pub',
                                       'ok': '99.901%',
                                       'unknown': '0.000%',
                                       'warning': '0.000%'},
                 'http_nova-api': {'critical': '0.433%',
                                   'name': 'http_nova-api',
                                   'ok': '99.567%',
                                   'unknown': '0.000%',
                                   'warning': '0.000%'},
                 'https': {'critical': '0.205%',
                           'name': 'https',
                           'ok': '99.795%',
                           'unknown': '0.000%',
                           'warning': '0.000%'}}})


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
               'services': [{'status': 'OK',
                             'duration': '20d 23h 41m 30s',
                             'display_name': 'Cinder',
                             'name': 'http_cinder-api',
                             'last_checked': '2014-10-06 13:57:38'}]},
              'accounts.rc.nectar.org.au':
              {'hostname': 'accounts.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '20d 23h 37m 32s',
                             'display_name': 'Webserver',
                             'name': 'https',
                             'last_checked': '2014-10-06 13:56:05'}]},
              'dashboard.rc.nectar.org.au':
              {'hostname': 'dashboard.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': ' 2d 18h 46m 57s',
                             'display_name': 'Webserver',
                             'name': 'https',
                             'last_checked': '2014-10-06 13:58:00'}]},
              'designate.rc.nectar.org.au':
              {'hostname': 'designate.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '19d 14h 57m 19s',
                             'display_name': 'Designate',
                             'name': 'http_designate-api',
                             'last_checked': '2014-10-06 13:58:43'}]},
              'glance-registry.rc.nectar.org.au':
              {'hostname': 'glance-registry.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '20d 23h 37m 36s',
                             'display_name': 'Glance Registry',
                             'name': 'http_glance-registry',
                             'last_checked': '2014-10-06 13:58:31'}]},
              'glance.rc.nectar.org.au':
              {'hostname': 'glance.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '18d 22h 57m  4s',
                             'display_name': 'Glance',
                             'name': 'http_glance-api',
                             'last_checked': '2014-10-06 13:58:17'}]},
              'heat.rc.nectar.org.au':
              {'hostname': 'heat.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '19d 14h 56m 49s',
                             'display_name': 'Heat',
                             'name': 'http_heat-api',
                             'last_checked': '2014-10-06 13:59:26'}]},
              'ceilometer.rc.nectar.org.au':
              {'hostname': 'ceilometer.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': ' 5d 21h  4m 57s',
                             'display_name': 'Ceilometer',
                             'name': 'http_ceilometer-api',
                             'last_checked': '2014-10-06 13:56:45'}]},
              'keystone.rc.nectar.org.au':
              {'hostname': 'keystone.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': '34d  0h 46m 14s',
                             'display_name': 'Keystone Admin',
                             'name': 'http_keystone-adm',
                             'last_checked': '2014-10-06 13:59:07'},
                            {'status': 'OK',
                             'duration': '33d 21h 20m 49s',
                             'display_name': 'Keystone',
                             'name': 'http_keystone-pub',
                             'last_checked': '2014-10-06 13:57:59'}]},
              'nova.rc.nectar.org.au':
              {'hostname': 'nova.rc.nectar.org.au',
               'services': [{'status': 'OK',
                             'duration': ' 2d 18h 43m 53s',
                             'display_name': 'EC2',
                             'name': 'http_ec2',
                             'last_checked': '2014-10-06 13:56:12'},
                            {'status': 'OK',
                             'duration': '35d  3h  5m 12s',
                             'display_name': 'Nova',
                             'name': 'http_nova-api',
                             'last_checked': '2014-10-06 13:56:08'}]}}})
