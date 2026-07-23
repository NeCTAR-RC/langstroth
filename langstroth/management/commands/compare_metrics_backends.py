"""Compare the Graphite and VictoriaMetrics backends endpoint by
endpoint.

The cutover acceptance test for the Graphite to VictoriaMetrics
migration: renders every growth/composition/user-statistics data
endpoint through BOTH backends (by overriding METRICS_BACKEND per
request) across the same range matrix the front-end uses, and diffs
the final JSON the browser would receive.

Growth series are index-aligned (both grids share the requested
from/until and step, but bucket timestamps may be offset by clock
drift or timezone config); the first and last buckets of each series
are exempt because summarize/avg_over_time legitimately disagree on
partial boundary buckets.
"""

import json

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.test.client import RequestFactory
from django.test.utils import override_settings

from langstroth.user_statistics import views as user_views
from langstroth import views


# Mirrors static/js/growth.js, plus archive-seam-straddling windows.
GROWTH_RANGES = [
    ('1hour', '-1day'),
    ('1hour', '-7days'),
    ('1hour', '-1months'),
    ('12hours', '-6months'),
    ('1days', '-1years'),
    ('3days', '-3years'),
    ('5days', '-5years'),
    ('10days', '20120101'),
    # retention-band seams (5m:7d and 10m:2y boundaries)
    ('1hour', '-8days'),
    ('12hours', '-26months'),
]
USER_RANGES = [
    (None, None),  # full history default
    ('20200101', None),
    (None, '-38months'),  # 1h:3y band seam
]


def close_enough(baseline, candidate, rel_tol, abs_tol):
    if baseline is None and candidate is None:
        return True
    if baseline is None or candidate is None:
        return False
    return abs(baseline - candidate) <= max(abs_tol, rel_tol * abs(baseline))


def compare_growth(baseline, candidate, rel_tol, abs_tol, skip_boundary=1):
    """Index-aligned comparison of growth series lists.

    Returns a list of failure strings (empty = pass).
    """
    failures = []
    b_targets = dict((s['target'], s['datapoints']) for s in baseline)
    c_targets = dict((s['target'], s['datapoints']) for s in candidate)
    if set(b_targets) != set(c_targets):
        failures.append(
            f"target sets differ: baseline={sorted(b_targets)} candidate={sorted(c_targets)}"
        )
        return failures

    for target in sorted(b_targets):
        b_dp = b_targets[target]
        c_dp = c_targets[target]
        extra = abs(len(b_dp) - len(c_dp))
        if extra > 1:
            # One backend covering a longer window is fine when the
            # extra leading buckets are empty (e.g. Graphite clamps
            # from= to the whisper retention while VictoriaMetrics
            # serves the full requested range as nulls/zero-fill).
            longer = b_dp if len(b_dp) > len(c_dp) else c_dp
            if not all(value in (None, 0) for value, _ in longer[:extra]):
                failures.append(
                    f"{target}: length mismatch {len(b_dp)} vs "
                    f"{len(c_dp)} with non-empty leading buckets"
                )
                continue
        # trim any extra leading boundary bucket, then index-align
        length = min(len(b_dp), len(c_dp))
        b_dp = b_dp[len(b_dp) - length :]
        c_dp = c_dp[len(c_dp) - length :]
        for i in range(skip_boundary, length - skip_boundary):
            b_val, c_val = b_dp[i][0], c_dp[i][0]
            if not close_enough(b_val, c_val, rel_tol, abs_tol):
                failures.append(
                    f"{target}[{i}] ts={b_dp[i][1]}/{c_dp[i][1]}: "
                    f"{b_val} != {c_val}"
                )
    return failures


def compare_composition(baseline, candidate, rel_tol, abs_tol):
    failures = []
    b_vals = dict((item['target'], item['value']) for item in baseline)
    c_vals = dict((item['target'], item['value']) for item in candidate)
    if set(b_vals) != set(c_vals):
        failures.append(
            f"group sets differ: baseline={sorted(b_vals)} candidate={sorted(c_vals)}"
        )
    for group in sorted(set(b_vals) & set(c_vals)):
        if not close_enough(b_vals[group], c_vals[group], rel_tol, abs_tol):
            failures.append(f"{group}: {b_vals[group]} != {c_vals[group]}")
    return failures


def compare_users(baseline, candidate, rel_tol, abs_tol, skip_boundary=1):
    """Timestamp-joined comparison of the (null-stripped) user
    statistics series."""
    failures = []
    b_targets = dict((s['target'], s['datapoints']) for s in baseline)
    c_targets = dict((s['target'], s['datapoints']) for s in candidate)
    if set(b_targets) != set(c_targets):
        failures.append(
            f"target sets differ: baseline={sorted(b_targets)} candidate={sorted(c_targets)}"
        )
        return failures
    for target in sorted(b_targets):
        b_map = dict((ts, val) for val, ts in b_targets[target])
        c_map = dict((ts, val) for val, ts in c_targets[target])
        shared = sorted(set(b_map) & set(c_map))
        one_sided = set(b_map) ^ set(c_map)
        # boundary leniency: a couple of one-sided points at the edges
        # of the range are bucket-alignment artefacts
        interior = [
            ts
            for ts in one_sided
            if shared
            and shared[skip_boundary] < ts < shared[-1 - skip_boundary]
        ]
        if not shared:
            failures.append(
                f"{target}: no shared timestamps (timezone "
                "mismatch between backends?)"
            )
            continue
        if interior:
            failures.append(
                f"{target}: {len(interior)} interior timestamps "
                f"present on only one side (e.g. {interior[:3]})"
            )
        for ts in shared[skip_boundary : len(shared) - skip_boundary]:
            if not close_enough(b_map[ts], c_map[ts], rel_tol, abs_tol):
                failures.append(
                    f"{target} ts={ts}: {b_map[ts]} != {c_map[ts]}"
                )
    return failures


class Command(BaseCommand):
    help = (
        "Diff the Graphite and VictoriaMetrics backends across "
        "the ranges the status page UI uses. Non-zero exit on "
        "any failing cell."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            default='all',
            choices=['all', 'instances', 'cores', 'composition', 'users'],
        )
        parser.add_argument('--tolerance-rel', type=float, default=0.005)
        parser.add_argument('--tolerance-abs', type=float, default=0.011)
        parser.add_argument(
            '--until',
            default='-1hours',
            help='Pinned until= for growth endpoints '
            '(relative or yyyymmdd), so both '
            'backends evaluate the same window.',
        )
        parser.add_argument(
            '--baseline-url', default=None, help='Override GRAPHITE_URL'
        )
        parser.add_argument(
            '--candidate-url',
            default=None,
            help='Override VICTORIAMETRICS_URL',
        )
        parser.add_argument('--max-failures-shown', type=int, default=5)

    def _render(self, backend, view, url, params, url_args=()):
        request = RequestFactory().get(url, params)
        with override_settings(METRICS_BACKEND=backend, **self.url_overrides):
            response = view(request, *url_args)
        if response.status_code != 200:
            raise CommandError(
                f"{backend} returned HTTP {response.status_code} "
                f"for {url} {params}"
            )
        return json.loads(response.content)

    def _run_cell(self, label, view, url, params, comparator, url_args=()):
        baseline = self._render('graphite', view, url, params, url_args)
        candidate = self._render(
            'victoriametrics', view, url, params, url_args
        )
        failures = comparator(baseline, candidate)
        status = 'FAIL' if failures else 'PASS'
        self.stdout.write(f"{status:<4} {label}")
        for failure in failures[: self.max_failures_shown]:
            self.stdout.write(f"       {failure}")
        if len(failures) > self.max_failures_shown:
            self.stdout.write(
                f"       ... and "
                f"{len(failures) - self.max_failures_shown} more"
            )
        return not failures

    def handle(self, *args, **options):
        from django.conf import settings

        rel = options['tolerance_rel']
        abs_tol = options['tolerance_abs']
        self.max_failures_shown = options['max_failures_shown']
        self.url_overrides = {}
        if options['baseline_url']:
            self.url_overrides['GRAPHITE_URL'] = options['baseline_url']
        if options['candidate_url']:
            self.url_overrides['VICTORIAMETRICS_URL'] = options[
                'candidate_url'
            ]

        def growth_cmp(b, c):
            return compare_growth(b, c, rel, abs_tol)

        def comp_cmp(b, c):
            return compare_composition(b, c, rel, abs_tol)

        def users_cmp(b, c):
            return compare_users(b, c, rel, abs_tol)

        endpoint = options['endpoint']
        ok = True

        if endpoint in ('all', 'instances', 'cores'):
            growth_views = []
            if endpoint in ('all', 'instances'):
                growth_views.append(
                    (
                        'instances',
                        views.total_instance_count,
                        '/growth/instance_count/',
                    )
                )
            if endpoint in ('all', 'cores'):
                growth_views.append(
                    ('cores', views.total_used_cores, '/growth/used_cores/')
                )
            for name, view, url in growth_views:
                for summarise, q_from in GROWTH_RANGES:
                    params = {
                        'from': q_from,
                        'until': options['until'],
                        'summarise': summarise,
                    }
                    label = f"{name} from={q_from} summarise={summarise}"
                    ok &= self._run_cell(label, view, url, params, growth_cmp)

        if endpoint in ('all', 'composition'):
            az_keys = sorted(
                set(
                    list(getattr(settings, 'COMPOSITION_QUERY', {}))
                    + list(settings.COMPOSITION_AZ_GROUPS)
                )
            )
            for name in ('domain', 'allocation_home'):
                for az in az_keys:
                    label = f"composition {name} az={az}"
                    ok &= self._run_cell(
                        label,
                        views.composition_cores,
                        f'/composition/{name}/cores',
                        {'az': az},
                        comp_cmp,
                        url_args=(name,),
                    )

        if endpoint in ('all', 'users'):
            for q_from, q_until in USER_RANGES:
                params = {}
                if q_from:
                    params['from'] = q_from
                if q_until:
                    params['until'] = q_until
                label = f"users from={q_from} until={q_until}"
                ok &= self._run_cell(
                    label,
                    user_views.registrations_frequency,
                    '/growth/users/rest/registrations/frequency',
                    params,
                    users_cmp,
                )

        if not ok:
            raise CommandError("One or more cells failed; see above.")
        self.stdout.write(self.style.SUCCESS("All cells passed."))
