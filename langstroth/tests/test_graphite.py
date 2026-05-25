from unittest import mock

from django.test import TestCase

from langstroth import graphite


class TargetTests(TestCase):
    def test_target(self):
        target = graphite.Target("test.az.something")
        self.assertEqual('test.az.something', str(target))
        self.assertIsInstance(target, graphite.Target)

    def test_target_equals(self):
        target0 = graphite.Target("test.az.something")
        target1 = graphite.Target("test.az.something")
        self.assertEqual(target0, target1)

    def test_target_not_equals(self):
        target0 = graphite.Target("test.az.something0")
        target1 = graphite.Target("test.az.something1")
        self.assertNotEqual(target0, target1)

    def test_target_not_equals_other_type(self):
        target = graphite.Target("test.az.something")
        self.assertFalse(target == "test.az.something")
        self.assertTrue(target != "test.az.something")

    def test_target_alias(self):
        target = graphite.Target("test.az.something").alias('name1')
        self.assertEqual('alias(test.az.something, "name1")', str(target))
        self.assertIsInstance(target, graphite.Target)

    def test_target_derivative(self):
        target = graphite.Target("test.az.something").derivative()
        self.assertEqual('derivative(test.az.something)', str(target))
        self.assertIsInstance(target, graphite.Target)

    def test_target_smart_summarize(self):
        target = graphite.Target("test.az.something")
        self.assertEqual(
            'smartSummarize(test.az.something, "1d", "avg")',
            str(target.smartSummarize('1d')),
        )
        self.assertEqual(
            'smartSummarize(test.az.something, "1d", "sum")',
            str(target.smartSummarize('1d', 'sum')),
        )
        # When step is None, original target is returned
        self.assertEqual('test.az.something', str(target.smartSummarize(None)))
        # When aggregation is empty
        self.assertEqual(
            'test.az.something', str(target.smartSummarize('1d', ''))
        )

    def test_target_summarize(self):
        target = graphite.Target("test.az.something")
        self.assertEqual(
            'summarize(test.az.something, "1d", "avg")',
            str(target.summarize('1d')),
        )
        self.assertEqual(
            'summarize(test.az.something, "1d", "sum")',
            str(target.summarize('1d', 'sum')),
        )
        self.assertEqual('test.az.something', str(target.summarize(None)))
        self.assertEqual('test.az.something', str(target.summarize('1d', '')))


class GraphiteGetTests(TestCase):
    @mock.patch('langstroth.graphite.requests.get')
    def test_get(self, mock_get):
        response = graphite.get(from_date='-1year')
        mock_get.assert_called_with(
            'http://graphite.dev.rc.nectar.org.au/render/?format=json&from=-1year',
            timeout=(5, 30),
        )
        self.assertEqual(mock_get(), response)

    @mock.patch('langstroth.graphite.requests.get')
    def test_get_with_until(self, mock_get):
        graphite.get(from_date='-1year', until_date='now')
        mock_get.assert_called_with(
            'http://graphite.dev.rc.nectar.org.au/render/'
            '?format=json&from=-1year&until=now',
            timeout=(5, 30),
        )

    @mock.patch('langstroth.graphite.requests.get')
    def test_get_target(self, mock_get):
        target = graphite.Target("test.az.something").alias("foo")
        graphite.get(from_date='-1year', targets=[target])
        mock_get.assert_called_with(
            'http://graphite.dev.rc.nectar.org.au/render/'
            '?format=json'
            '&target=alias%28test.az.something%2C+%22foo%22%29'
            '&from=-1year',
            timeout=(5, 30),
        )

    @mock.patch('langstroth.graphite.requests.get')
    def test_get_targets(self, mock_get):
        targets = [
            graphite.Target("test.az.something").alias("foo"),
            graphite.Target("test.az.something_else").alias("bar"),
        ]
        graphite.get(from_date='-1year', targets=targets)
        mock_get.assert_called_with(
            'http://graphite.dev.rc.nectar.org.au/render/'
            '?format=json'
            '&target=alias%28test.az.something%2C+%22foo%22%29'
            '&target=alias%28test.az.something_else%2C+%22bar%22%29'
            '&from=-1year',
            timeout=(5, 30),
        )


class FilterNullDatapointsTests(TestCase):
    def test_filter_strips_nulls(self):
        data = [
            {
                "target": "x",
                "datapoints": [
                    [None, 1],
                    [1.0, 2],
                    [None, 3],
                    [2.0, 4],
                ],
            }
        ]
        result = graphite.filter_null_datapoints(data)
        self.assertEqual([[1.0, 2], [2.0, 4]], result[0]['datapoints'])


class FillNullDatapointsTests(TestCase):
    def test_fill_basic(self):
        data = [
            {
                "datapoints": [
                    [None, 1324130400],
                    [1.0, 1324216800],
                    [3.0, 1325599200],
                    [None, 1413208800],
                ]
            }
        ]
        result = graphite.fill_null_datapoints(data)
        self.assertEqual(
            [
                [0.0, 1324130400],
                [1.0, 1324216800],
                [3.0, 1325599200],
                [3.0, 1413208800],
            ],
            result[0]['datapoints'],
        )

    def test_fill_picks_longest_template(self):
        data = [
            {"datapoints": [[1.0, 100], [2.0, 200]]},
            {"datapoints": [[5.0, 100], [6.0, 200], [7.0, 300]]},
        ]
        result = graphite.fill_null_datapoints(data)
        # both series end up with 3 points
        self.assertEqual(3, len(result[0]['datapoints']))
        self.assertEqual(3, len(result[1]['datapoints']))

    def test_fill_summarise_3days_resets_after_two_misses(self):
        # max_no_data is 2 for "3days"; once exceeded, previous_value
        # resets to 0.0
        tmpl_ts = list(range(1, 11))
        data = [
            {
                "datapoints": [[5.0, 1]] + [[None, t] for t in tmpl_ts[1:]],
            }
        ]
        result = graphite.fill_null_datapoints(data, summarise='3days')
        # First point is the original 5.0
        self.assertEqual(5.0, result[0]['datapoints'][0][0])
        # Should eventually drop to 0.0 after the threshold
        self.assertEqual(0.0, result[0]['datapoints'][-1][0])

    def test_fill_summarise_1days(self):
        data = [{"datapoints": [[1.0, 1]] + [[None, t] for t in range(2, 12)]}]
        graphite.fill_null_datapoints(data, summarise='1days')

    def test_fill_summarise_12hours(self):
        data = [{"datapoints": [[1.0, 1]] + [[None, t] for t in range(2, 20)]}]
        graphite.fill_null_datapoints(data, summarise='12hours')
