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
               'services': [{'duration': ' 6d 23h 25m 54s',
                             'display_name': 'Cinder',
                             'last_checked': '2014-06-30 10:48:23',
                             'name': 'http_cinder-api',
                             'status': 'OK'}]},
              'dashboard.rc.nectar.org.au':
              {'hostname': 'dashboard.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 25m 33s',
                             'display_name': 'Dashboard',
                             'last_checked': '2014-06-30 10:48:50',
                             'name': 'https',
                             'status': 'OK'}]},
              'designate.rc.nectar.org.au':
              {'hostname': 'designate.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h 49m 41s',
                             'display_name': 'Designate',
                             'last_checked': '2014-06-30 10:51:52',
                             'name': 'http_designate-api',
                             'status': 'OK'}]},
              'glance-registry.rc.nectar.org.au':
              {'hostname': 'glance-registry.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 27m 41s',
                             'display_name': 'Glance Registry',
                             'last_checked': '2014-06-30 10:48:50',
                             'name': 'http_glance-registry',
                             'status': 'OK'}]},
              'glance.rc.nectar.org.au':
              {'hostname': 'glance.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h  1m 18s',
                             'display_name': 'Glance',
                             'last_checked': '2014-06-30 10:49:12',
                             'name': 'http_glance-api',
                             'status': 'OK'}]},
              'heat.rc.nectar.org.au':
              {'hostname': 'heat.rc.nectar.org.au',
               'services': [{'duration': ' 5d 15h 53m 55s',
                             'display_name': 'Heat',
                             'last_checked': '2014-06-30 10:49:33',
                             'name': 'http_heat-api',
                             'status': 'OK'}]},
              'keystone.rc.nectar.org.au':
              {'hostname': 'keystone.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 25m 32s',
                             'display_name': 'Keystone Admin',
                             'last_checked': '2014-06-30 10:48:02',
                             'name': 'http_keystone-adm',
                             'status': 'OK'},
                            {'duration': ' 6d 23h 25m 11s',
                             'display_name': 'Keystone',
                             'last_checked': '2014-06-30 10:48:24',
                             'name': 'http_keystone-pub',
                             'status': 'OK'}]},
              'nova.rc.nectar.org.au':
              {'hostname': 'nova.rc.nectar.org.au',
               'services': [{'duration': ' 6d 23h 26m 58s',
                             'display_name': 'EC2',
                             'last_checked': '2014-06-30 10:50:44',
                             'name': 'http_ec2',
                             'status': 'OK'},
                            {'duration': ' 6d 23h 26m 37s',
                             'display_name': 'Nova',
                             'last_checked': '2014-06-30 10:51:07',
                             'name': 'http_nova-api',
                             'status': 'OK'}]}}})
