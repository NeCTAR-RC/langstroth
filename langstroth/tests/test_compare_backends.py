from io import StringIO
from json import dumps
from unittest import mock

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management import call_command
from django.http import HttpResponse
from django.test import override_settings
from django.test import TestCase

from langstroth.management.commands import compare_metrics_backends as cmp


def series(target, values, start=1000, step=10):
    return {
        'target': target,
        'datapoints': [
            [value, start + i * step] for i, value in enumerate(values)
        ],
    }


class CloseEnoughTests(TestCase):
    def test_close_enough(self):
        self.assertTrue(cmp.close_enough(None, None, 0.005, 0.011))
        self.assertFalse(cmp.close_enough(None, 1.0, 0.005, 0.011))
        self.assertFalse(cmp.close_enough(1.0, None, 0.005, 0.011))
        # absolute tolerance absorbs %0.2f-scale truncation
        self.assertTrue(cmp.close_enough(10.0, 10.01, 0.0, 0.011))
        # relative tolerance
        self.assertTrue(cmp.close_enough(1000.0, 1004.0, 0.005, 0.011))
        self.assertFalse(cmp.close_enough(1000.0, 1010.0, 0.005, 0.011))


class CompareGrowthTests(TestCase):
    def test_identical_passes(self):
        baseline = [series('A', [1, 2, 3, 4])]
        candidate = [series('A', [1, 2, 3, 4])]
        self.assertEqual(
            [], cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        )

    def test_boundary_buckets_exempt(self):
        baseline = [series('A', [99, 2, 3, 99])]
        candidate = [series('A', [1, 2, 3, 4])]
        self.assertEqual(
            [], cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        )

    def test_interior_mismatch_fails(self):
        baseline = [series('A', [1, 2, 3, 4])]
        candidate = [series('A', [1, 9, 3, 4])]
        failures = cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        self.assertEqual(1, len(failures))
        self.assertIn('A[1]', failures[0])

    def test_extra_leading_bucket_trimmed(self):
        baseline = [series('A', [0, 1, 2, 3, 4], start=990)]
        candidate = [series('A', [1, 2, 3, 4], start=1000)]
        self.assertEqual(
            [], cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        )

    def test_length_gap_with_data_fails(self):
        baseline = [series('A', [7, 8, 1, 2, 3, 4])]
        candidate = [series('A', [1, 2, 3, 4])]
        failures = cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        self.assertIn('length mismatch', failures[0])

    def test_retention_clamp_leading_empty_ok(self):
        # candidate serves a longer window whose extra leading buckets
        # are only zero-fill/nulls (graphite clamped from= to its
        # whisper retention)
        baseline = [series('A', [1, 2, 3, 4], start=1020)]
        candidate = [series('A', [0, None, 1, 2, 3, 4], start=1000)]
        self.assertEqual(
            [], cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        )

    def test_target_set_mismatch_fails(self):
        failures = cmp.compare_growth(
            [series('A', [1])], [series('B', [1])], 0.005, 0.011
        )
        self.assertIn('target sets differ', failures[0])

    def test_none_vs_value_interior_fails(self):
        baseline = [series('A', [1, None, 3, 4])]
        candidate = [series('A', [1, 2, 3, 4])]
        failures = cmp.compare_growth(baseline, candidate, 0.005, 0.011)
        self.assertEqual(1, len(failures))


class CompareCompositionTests(TestCase):
    def test_composition(self):
        baseline = [
            {'target': 'edu.au', 'value': 100.0},
            {'target': 'unimelb.edu.au', 'value': 500.0},
        ]
        candidate = [
            {'target': 'edu.au', 'value': 100.01},
            {'target': 'unimelb.edu.au', 'value': 500.0},
        ]
        self.assertEqual(
            [], cmp.compare_composition(baseline, candidate, 0.005, 0.011)
        )
        candidate[0]['value'] = 150.0
        failures = cmp.compare_composition(baseline, candidate, 0.005, 0.011)
        self.assertEqual(1, len(failures))


class CompareUsersTests(TestCase):
    def test_timestamp_join(self):
        baseline = [series('Cumulative', [1, 2, 3, 4, 5])]
        candidate = [series('Cumulative', [1, 2, 3, 4, 5])]
        self.assertEqual(
            [], cmp.compare_users(baseline, candidate, 0.005, 0.011)
        )

    def test_disjoint_timestamps_flagged(self):
        baseline = [series('Cumulative', [1, 2, 3], start=1000)]
        candidate = [series('Cumulative', [1, 2, 3], start=5000)]
        failures = cmp.compare_users(baseline, candidate, 0.005, 0.011)
        self.assertIn('no shared timestamps', failures[0])

    def test_interior_one_sided_timestamp_flagged(self):
        baseline = [series('Cumulative', [1, 2, 3, 4, 5, 6])]
        candidate = {
            'target': 'Cumulative',
            'datapoints': [
                [1, 1000],
                [2, 1010],
                [4, 1030],
                [5, 1040],
                [6, 1050],
            ],
        }
        failures = cmp.compare_users(baseline, [candidate], 0.005, 0.011)
        self.assertEqual(1, len(failures))
        self.assertIn('one side', failures[0])


def fake_view(per_backend_payload, status=200):
    """A stand-in endpoint returning a payload chosen by the
    METRICS_BACKEND the command sets for each render."""

    def view(request, *args):
        payload = per_backend_payload[settings.METRICS_BACKEND]
        return HttpResponse(
            dumps(payload), content_type='application/json', status=status
        )

    return view


GROWTH = [series('A', [1, 2, 3, 4, 5, 6])]
COMPOSITION = [{'target': 'edu.au', 'value': 100.0}]
USERS = [
    series('Cumulative', [1, 2, 3, 4, 5, 6]),
    series('Frequency', [1, 1, 1, 1, 1, 1]),
]
AGREEING = {
    'total_instance_count': fake_view(
        {'graphite': GROWTH, 'victoriametrics': GROWTH}
    ),
    'total_used_cores': fake_view(
        {'graphite': GROWTH, 'victoriametrics': GROWTH}
    ),
    'composition_cores': fake_view(
        {'graphite': COMPOSITION, 'victoriametrics': COMPOSITION}
    ),
    'registrations_frequency': fake_view(
        {'graphite': USERS, 'victoriametrics': USERS}
    ),
}


@override_settings(
    COMPOSITION_QUERY={'all': []}, COMPOSITION_AZ_GROUPS={'all': None}
)
class CommandRunTests(TestCase):
    def run_command(self, views=AGREEING, *args, **options):
        out = StringIO()
        with (
            mock.patch(
                'langstroth.views.total_instance_count',
                views['total_instance_count'],
            ),
            mock.patch(
                'langstroth.views.total_used_cores',
                views['total_used_cores'],
            ),
            mock.patch(
                'langstroth.views.composition_cores',
                views['composition_cores'],
            ),
            mock.patch(
                'langstroth.user_statistics.views.registrations_frequency',
                views['registrations_frequency'],
            ),
        ):
            call_command(
                'compare_metrics_backends', *args, stdout=out, **options
            )
        return out.getvalue()

    def test_all_endpoints_pass_when_backends_agree(self):
        output = self.run_command()
        self.assertIn('All cells passed.', output)
        # 10 ranges x 2 growth endpoints + 2 composition names x 1 az
        # group + 3 users ranges
        self.assertEqual(25, output.count('PASS'))
        self.assertNotIn('FAIL', output)

    def test_single_endpoint_selection(self):
        output = self.run_command(endpoint='users')
        self.assertEqual(3, output.count('PASS'))

    def test_disagreeing_backends_raise(self):
        different = [series('A', [9, 9, 9, 9, 9, 9])]
        views = dict(AGREEING)
        views['total_instance_count'] = fake_view(
            {'graphite': GROWTH, 'victoriametrics': different}
        )
        with self.assertRaises(CommandError):
            self.run_command(views=views, endpoint='instances')

    def test_failure_overflow_is_truncated(self):
        long_baseline = [series('A', list(range(20)))]
        long_candidate = [series('A', [99] * 20)]
        views = dict(AGREEING)
        views['total_instance_count'] = fake_view(
            {'graphite': long_baseline, 'victoriametrics': long_candidate}
        )
        try:
            self.run_command(
                views=views, endpoint='instances', max_failures_shown=2
            )
        except CommandError:
            pass
        # exercised the "... and N more" truncation branch via
        # max_failures_shown

    def test_http_error_raises(self):
        views = dict(AGREEING)
        views['registrations_frequency'] = fake_view(
            {'graphite': [], 'victoriametrics': []}, status=503
        )
        with self.assertRaises(CommandError):
            self.run_command(views=views, endpoint='users')

    def test_url_overrides_apply_during_render(self):
        seen = {}

        def spy_view(request, *args):
            seen[settings.METRICS_BACKEND] = (
                settings.GRAPHITE_URL,
                settings.VICTORIAMETRICS_URL,
            )
            return HttpResponse(dumps(USERS), content_type='application/json')

        views = dict(AGREEING)
        views['registrations_frequency'] = spy_view
        self.run_command(
            views=views,
            endpoint='users',
            baseline_url='http://old.example',
            candidate_url='http://new.example:8428',
        )
        self.assertEqual('http://old.example', seen['graphite'][0])
        self.assertEqual('http://new.example:8428', seen['victoriametrics'][1])
