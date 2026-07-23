import json
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import urlparse

from django.test import override_settings
from django.test import TestCase

from langstroth import metrics


# Divisible by 86400 so the step-aligned query grids in these tests
# match the raw start/end values.
NOW = 1784764800


def fake_response(result):
    response = mock.Mock()
    response.json.return_value = {
        'status': 'success',
        'data': {'result': result},
    }
    return response


class TimeParsingTests(TestCase):
    def test_window_seconds(self):
        self.assertEqual(3600, metrics.window_seconds('1hour'))
        self.assertEqual(43200, metrics.window_seconds('12hours'))
        self.assertEqual(86400, metrics.window_seconds('1days'))
        self.assertEqual(864000, metrics.window_seconds('10days'))
        self.assertEqual(15552000, metrics.window_seconds('-6months'))
        self.assertEqual(31536000, metrics.window_seconds('-1years'))

    def test_window_seconds_invalid(self):
        with self.assertRaises(ValueError):
            metrics.window_seconds('drop table')

    def test_parse_time_relative(self):
        self.assertEqual(NOW - 86400, metrics.parse_time('-1day', NOW))
        self.assertEqual(NOW, metrics.parse_time(None, NOW))

    @override_settings(TIME_ZONE='UTC')
    def test_parse_time_absolute_utc(self):
        # 2012-01-01T00:00:00Z
        self.assertEqual(1325376000, metrics.parse_time('20120101', NOW))


@mock.patch('langstroth.metrics._SESSION.get')
@override_settings(VICTORIAMETRICS_URL='http://vm.test:8428')
class AggregateSeriesTests(TestCase):
    def test_query_and_reshape(self, mock_get):
        start = NOW - 43200
        # evaluation timestamps are window ENDS: one step ahead of the
        # bucket-start labels the response is reshaped to
        mock_get.return_value = fake_response(
            [
                {
                    'metric': {},
                    'values': [[start + 3600, '10'], [start + 7200, '11.5']],
                }
            ]
        )
        data = metrics.aggregate_series(
            'nectar_total_instances',
            [('Melbourne', ['melbourne-qh2', 'melbourne-np'])],
            from_date='-12hours',
            summarise='1hour',
            now=NOW,
        )

        url = mock_get.call_args[0][0]
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual('/api/v1/query_range', parsed.path)
        self.assertEqual(
            [
                'sum(avg_over_time(nectar_total_instances'
                '{az=~"melbourne\\-qh2|melbourne\\-np"}[3600s] offset 1s))'
            ],
            params['query'],
        )
        # queried one step ahead so the [end, end+step) bucket exists
        self.assertEqual([str(start + 3600)], params['start'])
        self.assertEqual([str(NOW + 3600)], params['end'])
        self.assertEqual(['3600'], params['step'])

        self.assertEqual(1, len(data))
        self.assertEqual('Melbourne', data[0]['target'])
        datapoints = data[0]['datapoints']
        # full grid start..end inclusive with nulls for missing steps
        self.assertEqual(13, len(datapoints))
        self.assertEqual([10.0, start], datapoints[0])
        self.assertEqual([11.5, start + 3600], datapoints[1])
        self.assertEqual([None, start + 7200], datapoints[2])
        self.assertEqual([None, NOW], datapoints[-1])

    def test_all_azs_selector(self, mock_get):
        mock_get.return_value = fake_response([])
        metrics.aggregate_series(
            'nectar_used_vcpus',
            [('All', None)],
            from_date='-1day',
            summarise='1hour',
            now=NOW,
        )
        url = mock_get.call_args[0][0]
        params = parse_qs(urlparse(url).query)
        self.assertIn('az=~".+"', params['query'][0])

    def test_zero_summarise_raises(self, mock_get):
        # summarise=0days passes the views' sanitiser; a zero step must
        # raise ValueError (-> 503) rather than ZeroDivisionError (-> 500)
        with self.assertRaises(ValueError):
            metrics.aggregate_series(
                'nectar_used_vcpus',
                [('All', None)],
                from_date='-1day',
                summarise='0hours',
                now=NOW,
            )
        mock_get.assert_not_called()

    def test_error_status_raises(self, mock_get):
        response = mock.Mock()
        response.json.return_value = {'status': 'error', 'error': 'boom'}
        mock_get.return_value = response
        with self.assertRaises(ValueError):
            metrics.aggregate_series(
                'nectar_used_vcpus',
                [('All', None)],
                from_date='-1day',
                now=NOW,
            )


@mock.patch('langstroth.metrics._SESSION.get')
@override_settings(VICTORIAMETRICS_URL='http://vm.test:8428')
class CompositionTests(TestCase):
    def test_composition_values(self, mock_get):
        mock_get.return_value = fake_response(
            [
                {
                    'metric': {'domain': 'unimelb.edu.au'},
                    'value': [NOW, '500'],
                },
                {'metric': {'domain': 'edu.au'}, 'value': [NOW, '100']},
            ]
        )
        data = metrics.composition_values('domain', ['melbourne-qh2'], now=NOW)
        url = mock_get.call_args[0][0]
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        self.assertEqual('/api/v1/query', parsed.path)
        self.assertEqual(
            [
                'sum by (domain) (last_over_time(nectar_domain_used_vcpus'
                '{az=~"melbourne\\-qh2"}[1h]))'
            ],
            params['query'],
        )
        # sorted ascending by value, label used as target
        self.assertEqual(
            [
                {'target': 'edu.au', 'value': 100.0},
                {'target': 'unimelb.edu.au', 'value': 500.0},
            ],
            data,
        )

    def test_allocation_home_metric(self, mock_get):
        mock_get.return_value = fake_response([])
        metrics.composition_values('allocation_home', None, now=NOW)
        params = parse_qs(urlparse(mock_get.call_args[0][0]).query)
        self.assertIn('nectar_allocation_home_used_vcpus', params['query'][0])
        self.assertIn('sum by (home)', params['query'][0])

    def test_unknown_name_is_empty(self, mock_get):
        self.assertEqual([], metrics.composition_values('junk', None, now=NOW))
        mock_get.assert_not_called()


@mock.patch('langstroth.metrics._SESSION.get')
@override_settings(VICTORIAMETRICS_URL='http://vm.test:8428', TIME_ZONE='UTC')
class UserStatisticsTests(TestCase):
    def test_cumulative_and_frequency(self, mock_get):
        start = metrics.parse_time('20200101', NOW)
        # window-end evaluation timestamps, one step ahead of the
        # bucket starts asserted below
        mock_get.return_value = fake_response(
            [
                {
                    'metric': {},
                    'values': [
                        [start + 86400, '100'],
                        [start + 2 * 86400, '110'],
                        # gap at start + 2 * 86400 (bucket-start labelling)
                        [start + 4 * 86400, '130'],
                    ],
                }
            ]
        )
        data = metrics.user_statistics_series(
            '20200101', until_date=None, now=NOW
        )
        params = parse_qs(urlparse(mock_get.call_args[0][0]).query)
        self.assertEqual(
            ['max_over_time(nectar_users_total[1d] offset 1s)'],
            params['query'],
        )
        self.assertEqual(['86400'], params['step'])

        self.assertEqual('Cumulative', data[0]['target'])
        self.assertEqual('Frequency', data[1]['target'])
        cumulative = data[0]['datapoints']
        frequency = data[1]['datapoints']
        self.assertEqual([100.0, start], cumulative[0])
        self.assertEqual([110.0, start + 86400], cumulative[1])
        self.assertEqual([None, start + 2 * 86400], cumulative[2])
        self.assertEqual([130.0, start + 3 * 86400], cumulative[3])
        # derivative: first point None, gap blanks itself AND the
        # following point (graphite semantics)
        self.assertEqual([None, start], frequency[0])
        self.assertEqual([10.0, start + 86400], frequency[1])
        self.assertEqual([None, start + 2 * 86400], frequency[2])
        self.assertEqual([None, start + 3 * 86400], frequency[3])

    def test_json_shape_round_trips(self, mock_get):
        mock_get.return_value = fake_response([])
        data = metrics.user_statistics_series('20200101', now=NOW)
        # must serialise to the legacy JSON contract
        parsed = json.loads(json.dumps(data))
        self.assertEqual(
            ['Cumulative', 'Frequency'],
            [series['target'] for series in parsed],
        )
