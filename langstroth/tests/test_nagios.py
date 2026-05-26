import datetime
import os
from unittest import mock

from django.conf import settings
from django.test import override_settings
from django.test import TestCase

from langstroth import nagios


DIR = os.path.abspath(os.path.dirname(__file__))


class TestNagios(TestCase):
    def test_parse_percent_string(self):
        value = '1.123%'
        result = nagios.parse_percent_string(value)
        self.assertEqual(result, 1.123)

    def test_parse_percent_string_invalid_returns_none(self):
        # Unparseable input (e.g. Nagios "N/A") returns None so callers
        # can distinguish "no data" from "actually zero".
        self.assertIsNone(nagios.parse_percent_string('bad_value'))
        self.assertIsNone(nagios.parse_percent_string('N/A'))
        self.assertIsNone(nagios.parse_percent_string(None))


class TestAvailability(TestCase):
    maxDiff = None

    def test_parsing(self):
        html = open(os.path.join(DIR, 'test_availability.html'), 'rb').read()
        result = nagios.parse_availability(html, settings.NAGIOS_SERVICE_GROUP)
        self.assertEqual(
            result,
            {
                'average': {'critical': 0.14, 'name': 'Average', 'ok': 99.860},
                'services': {
                    'http_cinder-api': {
                        'critical': 0.055,
                        'name': 'http_cinder-api',
                        'ok': 99.945,
                    },
                    'http_designate-api': {
                        'critical': 0.0,
                        'name': 'http_designate-api',
                        'ok': 100.0,
                    },
                    'http_ec2': {
                        'critical': 0.413,
                        'name': 'http_ec2',
                        'ok': 99.587,
                    },
                    'http_glance-api': {
                        'critical': 0.018,
                        'name': 'http_glance-api',
                        'ok': 99.982,
                    },
                    'http_glance-registry': {
                        'critical': 0.103,
                        'name': 'http_glance-registry',
                        'ok': 99.897,
                    },
                    'http_heat-api': {
                        'critical': 0.0,
                        'name': 'http_heat-api',
                        'ok': 100.0,
                    },
                    'http_keystone-adm': {
                        'critical': 0.074,
                        'name': 'http_keystone-adm',
                        'ok': 99.926,
                    },
                    'http_keystone-pub': {
                        'critical': 0.099,
                        'name': 'http_keystone-pub',
                        'ok': 99.901,
                    },
                    'http_nova-api': {
                        'critical': 0.433,
                        'name': 'http_nova-api',
                        'ok': 99.567,
                    },
                    'https': {
                        'critical': 0.205,
                        'name': 'https',
                        'ok': 99.795,
                    },
                },
            },
        )


class TestStatus(TestCase):
    maxDiff = None

    def test_parsing(self):
        html = open(os.path.join(DIR, 'test_status.html')).read()
        result = nagios.parse_status(html, settings.NAGIOS_SERVICE_GROUP)
        self.assertEqual(
            result,
            {
                'hosts': {
                    'cinder.rc.nectar.org.au': {
                        'hostname': 'cinder.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '20d 23h 41m 30s',
                                'display_name': 'Volume',
                                'name': 'http_cinder-api',
                                'last_checked': '2014-10-06 13:57:38',
                            }
                        ],
                    },
                    'accounts.rc.nectar.org.au': {
                        'hostname': 'accounts.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '20d 23h 37m 32s',
                                'display_name': 'Accounts',
                                'name': 'http_accounts',
                                'last_checked': '2014-10-06 13:56:05',
                            }
                        ],
                    },
                    'dashboard.rc.nectar.org.au': {
                        'hostname': 'dashboard.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': ' 2d 18h 46m 57s',
                                'display_name': 'Dashboard',
                                'name': 'http_dashboard',
                                'last_checked': '2014-10-06 13:58:00',
                            }
                        ],
                    },
                    'designate.rc.nectar.org.au': {
                        'hostname': 'designate.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '19d 14h 57m 19s',
                                'display_name': 'DNS',
                                'name': 'http_designate-api',
                                'last_checked': '2014-10-06 13:58:43',
                            }
                        ],
                    },
                    'glance-registry.rc.nectar.org.au': {
                        'hostname': 'glance-registry.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '20d 23h 37m 36s',
                                'display_name': 'Image Registry',
                                'name': 'http_glance-registry',
                                'last_checked': '2014-10-06 13:58:31',
                            }
                        ],
                    },
                    'glance.rc.nectar.org.au': {
                        'hostname': 'glance.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '18d 22h 57m  4s',
                                'display_name': 'Image',
                                'name': 'http_glance-api',
                                'last_checked': '2014-10-06 13:58:17',
                            }
                        ],
                    },
                    'heat.rc.nectar.org.au': {
                        'hostname': 'heat.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '19d 14h 56m 49s',
                                'display_name': 'Orchestration',
                                'name': 'http_heat-api',
                                'last_checked': '2014-10-06 13:59:26',
                            }
                        ],
                    },
                    'ceilometer.rc.nectar.org.au': {
                        'hostname': 'ceilometer.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': ' 5d 21h  4m 57s',
                                'display_name': 'Ceilometer',
                                'name': 'http_ceilometer-api',
                                'last_checked': '2014-10-06 13:56:45',
                            }
                        ],
                    },
                    'keystone.rc.nectar.org.au': {
                        'hostname': 'keystone.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': '33d 21h 20m 49s',
                                'display_name': 'Identity',
                                'name': 'http_keystone-pub',
                                'last_checked': '2014-10-06 13:57:59',
                            }
                        ],
                    },
                    'nova.rc.nectar.org.au': {
                        'hostname': 'nova.rc.nectar.org.au',
                        'services': [
                            {
                                'status': 'OK',
                                'duration': ' 2d 18h 43m 53s',
                                'display_name': 'EC2',
                                'name': 'http_ec2',
                                'last_checked': '2014-10-06 13:56:12',
                            },
                            {
                                'status': 'OK',
                                'duration': '35d  3h  5m 12s',
                                'display_name': 'Compute',
                                'name': 'http_nova-api',
                                'last_checked': '2014-10-06 13:56:08',
                            },
                        ],
                    },
                }
            },
        )


class TestParsingFallbacks(TestCase):
    def test_parse_availability_no_matching_group(self):
        html = open(os.path.join(DIR, 'test_availability.html'), 'rb').read()
        result = nagios.parse_availability(html, 'nonexistent_group')
        self.assertEqual({'services': {}, 'average': {}}, result)

    def test_parse_status_no_matching_group(self):
        html = open(os.path.join(DIR, 'test_status.html')).read()
        result = nagios.parse_status(html, 'nonexistent_group')
        self.assertEqual({'hosts': {}}, result)


class TestRequestCallers(TestCase):
    def test_gm_timestamp(self):
        # tz-aware UTC datetime
        ts = nagios.gm_timestamp(
            datetime.datetime(
                2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            )
        )
        self.assertEqual(1704067200, ts)

    def test_gm_timestamp_aware_non_utc(self):
        # Aware datetime in a non-UTC offset returns the correct UTC
        # epoch (the offset is honoured, not stripped).
        plus_ten = datetime.timezone(datetime.timedelta(hours=10))
        ts = nagios.gm_timestamp(
            datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=plus_ten)
        )
        self.assertEqual(1704067200, ts)

    def test_gm_timestamp_rejects_naive(self):
        with self.assertRaises(TypeError):
            nagios.gm_timestamp(datetime.datetime(2024, 1, 1, 0, 0, 0))

    @override_settings(
        AVAILABILITY_QUERY_TEMPLATE="?t1=%s&t2=%s&group=%s",
        STATUS_QUERY_TEMPLATE="?group=%s",
    )
    @mock.patch('langstroth.nagios._SESSION.get')
    def test_get_availability(self, mock_get):
        html = open(os.path.join(DIR, 'test_availability.html'), 'rb').read()
        mock_get.return_value = mock.Mock(text=html)
        result = nagios.get_availability(
            datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
            datetime.datetime(2024, 1, 2, tzinfo=datetime.timezone.utc),
            service_group=settings.NAGIOS_SERVICE_GROUP,
        )
        self.assertIn('services', result)
        mock_get.assert_called_once()

    @override_settings(
        AVAILABILITY_QUERY_TEMPLATE="?t1=%s&t2=%s&group=%s",
        STATUS_QUERY_TEMPLATE="?group=%s",
    )
    @mock.patch('langstroth.nagios._SESSION.get')
    def test_get_status(self, mock_get):
        html = open(os.path.join(DIR, 'test_status.html')).read()
        mock_get.return_value = mock.Mock(text=html)
        result = nagios.get_status(service_group=settings.NAGIOS_SERVICE_GROUP)
        self.assertIn('hosts', result)
        mock_get.assert_called_once()
