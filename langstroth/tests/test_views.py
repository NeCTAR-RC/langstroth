import os
from unittest.mock import call
from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory
from django.test import TestCase

from langstroth import nagios
from langstroth import views

DIR = os.path.abspath(os.path.dirname(__file__))


def _load_html(name):
    return open(os.path.join(DIR, f"test_{name}.html"), 'rb').read()


class TestViews(TestCase):

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.availability_f5 = nagios.parse_availability(
            _load_html("availability_f5"), settings.NAGIOS_SERVICE_GROUP)
        self.availability_tempest = nagios.parse_availability(
            _load_html("availability_tempest"), 'tempest_compute_site')
        self.status_f5 = nagios.parse_status(
            _load_html("status_f5"), settings.NAGIOS_SERVICE_GROUP)
        self.status_tempest = nagios.parse_status(
            _load_html("status_tempest"), 'tempest_compute_site')
        self.rf = RequestFactory()

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    def test_cache_miss(self, mock_cache, mock_get_status,
                        mock_get_availability):
        "Check that cache and nagios calls are made on cache miss"

        mock_get_availability.side_effect = [
            self.availability_f5, self.availability_tempest]
        mock_get_status.side_effect = [
            self.status_f5, self.status_tempest]
        mock_cache.get.return_value = None   # All miss
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        response = views.index(request)
        self.assertEqual(200, response.status_code)
        range = "2024-06-17_2024-05-17"
        mock_cache.get.assert_has_calls([
            call(f'_nagios_availability_f5-endpoints_{range}'),
            call('nagios_status_f5-endpoints'),
            call(f'_nagios_availability_tempest_compute_site_{range}'),
            call('nagios_status_tempest_compute_site')
        ], any_order=True)
        self.assertEqual(4, mock_cache.get.call_count)

        mock_cache.set.assert_has_calls([
            call(f'_nagios_availability_f5-endpoints_{range}',
                 self.availability_f5, 600),
            call(f'nagios_availability_f5-endpoints_{range}',
                 self.availability_f5),
            call(f'_nagios_availability_tempest_compute_site_{range}',
                 self.availability_tempest, 600),
            call(f'nagios_availability_tempest_compute_site_{range}',
                 self.availability_tempest),
        ], any_order=True)
        self.assertEqual(6, mock_cache.set.call_count)

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    @patch('langstroth.views.LOG')
    def test_cache_miss_and_fail(self, mock_log, mock_cache, mock_get_status,
                                 mock_get_availability):
        """Check that cache and nagios calls are made on cache miss
        with simulated nagios failures.
        """

        mock_get_availability.side_effect = Exception("Nagios error")
        mock_get_status.side_effect = Exception("Nagios error")
        mock_cache.get.side_effect = [
            None, self.availability_f5, None,
            None, self.availability_tempest, None]
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        response = views.index(request)
        self.assertEqual(200, response.status_code)
        range = "2024-06-17_2024-05-17"
        mock_cache.get.assert_has_calls([
            call(f'_nagios_availability_f5-endpoints_{range}'),
            call(f'nagios_availability_f5-endpoints_{range}'),
            call('nagios_status_f5-endpoints'),
            call(f'_nagios_availability_tempest_compute_site_{range}'),
            call(f'nagios_availability_tempest_compute_site_{range}'),
            call('nagios_status_tempest_compute_site')
        ], any_order=True)
        self.assertEqual(6, mock_cache.get.call_count)

        mock_cache.set.assert_not_called()
        mock_get_status.assert_called()
        mock_get_availability.assert_called()
        mock_log.error.assert_called()

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    def test_cache_hits(self, mock_cache, mock_get_status,
                        mock_get_availability):
        "Check that cache and nagios calls are made on cache hit"

        mock_cache.get.side_effect = [
            self.availability_f5, self.status_f5,
            self.availability_tempest, self.status_tempest]
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        response = views.index(request)
        self.assertEqual(200, response.status_code)
        range = "2024-06-17_2024-05-17"
        mock_cache.get.assert_has_calls([
            call(f'_nagios_availability_f5-endpoints_{range}'),
            call('nagios_status_f5-endpoints'),
            call(f'_nagios_availability_tempest_compute_site_{range}'),
            call('nagios_status_tempest_compute_site')
        ], any_order=True)
        self.assertEqual(4, mock_cache.get.call_count)

        mock_cache.set.assert_not_called()
        mock_get_status.assert_not_called()
        mock_get_availability.assert_not_called()

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    @patch('langstroth.views.render')
    def test_context(self, mock_render, mock_cache,
                     mock_get_status, mock_get_availability):
        "Check the values placed in the rendering context"

        mock_get_availability.side_effect = [
            self.availability_f5, self.availability_tempest]
        mock_get_status.side_effect = [
            self.status_f5, self.status_tempest]
        mock_cache.get.return_value = None
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        _ = views.index(request)
        name, args, kwargs = mock_render.mock_calls[0]
        self.assertEqual(request, args[0])
        self.assertEqual("index.html", args[1])
        context = args[2]
        self.assertEqual("OK", context['overall_status'])
        self.assertEqual('17 May 2024 to 17 Jun 2024', context['tagline'])

        # (These values haven't been validated ...)
        self.assertEqual(25, len(context['api_hosts']))
        self.assertEqual(1, len(context['site_hosts']))
        self.assertEqual(9, len(context['site_hosts'][0]['services']))
        self.assertEqual({'name': 'Average', 'ok': 99.897, 'critical': 0.103},
                         context['api_average'])
        self.assertEqual({'name': 'Average', 'ok': 99.727, 'critical': 0.273},
                         context['site_average'])

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    @patch('langstroth.views.render')
    def test_api_down(self, mock_render, mock_cache,
                      mock_get_status, mock_get_availability):
        "Check that we are detecting API services down"

        self.status_f5['hosts']['accounts.rc.nectar.org.au'][
            'services'][0]['status'] = 'Critical'

        mock_get_availability.side_effect = [
            self.availability_f5, self.availability_tempest]
        mock_get_status.side_effect = [
            self.status_f5, self.status_tempest]
        mock_cache.get.return_value = None
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        _ = views.index(request)
        name, args, kwargs = mock_render.mock_calls[0]
        self.assertEqual(request, args[0])
        self.assertEqual("index.html", args[1])
        context = args[2]
        self.assertEqual("Critical", context['overall_status'])
        self.assertEqual('17 May 2024 to 17 Jun 2024', context['tagline'])

    @patch('langstroth.views.get_availability')
    @patch('langstroth.views.get_status')
    @patch('langstroth.views.cache')
    @patch('langstroth.views.render')
    def test_tempest_down(self, mock_render, mock_cache,
                          mock_get_status, mock_get_availability):
        "Check that we are detecting tempest host down"

        self.status_tempest['hosts']['tempest.rc.nectar.org.au'][
            'services'][0]['status'] = 'Critical'

        mock_get_availability.side_effect = [
            self.availability_f5, self.availability_tempest]
        mock_get_status.side_effect = [
            self.status_f5, self.status_tempest]
        mock_cache.get.return_value = None
        request = self.rf.get("/", {'start': '2024-05-17',
                                    'end': '2024-06-17'})
        _ = views.index(request)
        name, args, kwargs = mock_render.mock_calls[0]
        self.assertEqual(request, args[0])
        self.assertEqual("index.html", args[1])
        context = args[2]
        self.assertEqual("Critical", context['overall_status'])
        self.assertEqual('17 May 2024 to 17 Jun 2024', context['tagline'])
