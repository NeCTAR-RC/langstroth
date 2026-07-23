"""Tests for the VictoriaMetrics branches of the metrics views and
the user statistics service."""

from json import loads
from unittest import mock

from django.test import override_settings
from django.test import TestCase
import requests

from langstroth.user_statistics.services import user_statistics


SERIES = [
    {
        'target': 'Melbourne',
        'datapoints': [[1.0, 1000], [2.0, 1010], [3.0, 1020]],
    }
]
COMPOSITION = [
    {'target': 'edu.au', 'value': 100.0},
    {'target': 'unimelb.edu.au', 'value': 500.0},
]


@override_settings(
    METRICS_BACKEND='victoriametrics',
    INST_SERIES=[('Melbourne', ['melbourne-qh2'])],
    CORES_SERIES=[('Melbourne', ['melbourne-qh2'])],
    COMPOSITION_AZ_GROUPS={'all': None, 'melbourne': ['melbourne-qh2']},
)
class VictoriaGrowthViewTests(TestCase):
    @mock.patch('langstroth.metrics.aggregate_series')
    def test_instance_count(self, mock_agg):
        mock_agg.return_value = [
            {'target': s['target'], 'datapoints': list(s['datapoints'])}
            for s in SERIES
        ]
        response = self.client.get(
            '/growth/instance_count/?from=-1day&summarise=1hour'
        )
        self.assertEqual(200, response.status_code)
        data = loads(response.content)
        self.assertEqual('Melbourne', data[0]['target'])
        self.assertEqual(
            [[1.0, 1000], [2.0, 1010], [3.0, 1020]], data[0]['datapoints']
        )
        mock_agg.assert_called_once_with(
            'nectar_total_instances',
            [('Melbourne', ['melbourne-qh2'])],
            from_date='-1day',
            until_date=None,
            summarise='1hour',
        )

    @mock.patch('langstroth.metrics.aggregate_series')
    def test_used_cores(self, mock_agg):
        mock_agg.return_value = []
        response = self.client.get('/growth/used_cores/')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], loads(response.content))
        self.assertEqual('nectar_used_vcpus', mock_agg.call_args[0][0])

    @mock.patch('langstroth.metrics.aggregate_series')
    def test_backend_error_returns_503(self, mock_agg):
        mock_agg.side_effect = requests.ConnectionError('down')
        response = self.client.get('/growth/instance_count/')
        self.assertEqual(503, response.status_code)
        self.assertEqual([], loads(response.content))

    def test_zero_summarise_returns_503(self):
        # no mock: aggregate_series rejects the zero step before it
        # would touch the network
        response = self.client.get('/growth/instance_count/?summarise=0days')
        self.assertEqual(503, response.status_code)
        self.assertEqual([], loads(response.content))


@override_settings(
    METRICS_BACKEND='victoriametrics',
    COMPOSITION_AZ_GROUPS={'all': None, 'melbourne': ['melbourne-qh2']},
)
class VictoriaCompositionViewTests(TestCase):
    @mock.patch('langstroth.metrics.composition_values')
    def test_known_az_group(self, mock_comp):
        mock_comp.return_value = COMPOSITION
        response = self.client.get('/composition/domain/cores?az=melbourne')
        self.assertEqual(200, response.status_code)
        self.assertEqual(COMPOSITION, loads(response.content))
        mock_comp.assert_called_once_with('domain', ['melbourne-qh2'])

    @mock.patch('langstroth.metrics.composition_values')
    def test_unknown_az_falls_back_to_single_az(self, mock_comp):
        mock_comp.return_value = []
        response = self.client.get('/composition/domain/cores?az=qld')
        self.assertEqual(200, response.status_code)
        mock_comp.assert_called_once_with('domain', ['qld'])

    @mock.patch('langstroth.metrics.composition_values')
    def test_backend_error_returns_503(self, mock_comp):
        mock_comp.side_effect = requests.ConnectionError('down')
        response = self.client.get('/composition/domain/cores')
        self.assertEqual(503, response.status_code)


@override_settings(
    METRICS_BACKEND='victoriametrics',
    USER_STATISTICS_START_DATE='20200101',
)
class VictoriaUserStatisticsServiceTests(TestCase):
    @mock.patch('langstroth.metrics.user_statistics_series')
    def test_success_strips_nulls(self, mock_series):
        mock_series.return_value = [
            {
                'target': 'Cumulative',
                'datapoints': [[None, 990], [100.0, 1000]],
            },
            {
                'target': 'Frequency',
                'datapoints': [[None, 990], [1.0, 1000]],
            },
        ]
        data = user_statistics.find_daily_accumulated_users()
        mock_series.assert_called_once_with('20200101', None)
        self.assertEqual([[100.0, 1000]], data[0]['datapoints'])
        self.assertEqual([[1.0, 1000]], data[1]['datapoints'])

    @mock.patch('langstroth.metrics.user_statistics_series')
    def test_explicit_range_passed_through(self, mock_series):
        mock_series.return_value = []
        user_statistics.find_daily_accumulated_users('20210101', '20220101')
        mock_series.assert_called_once_with('20210101', '20220101')

    @mock.patch('langstroth.metrics.user_statistics_series')
    def test_backend_error_returns_empty(self, mock_series):
        mock_series.side_effect = requests.ConnectionError('down')
        self.assertEqual([], user_statistics.find_daily_accumulated_users())
