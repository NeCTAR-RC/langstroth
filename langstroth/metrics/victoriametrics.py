"""VictoriaMetrics backend for the growth, composition and user
statistics pages.

Queries the Prometheus-compatible /api/v1/query_range and
/api/v1/query endpoints with MetricsQL and reshapes the responses to
the JSON structures described in langstroth.metrics ([{"target": ...,
"datapoints": [[value|null, ts], ...]}] -- originally the Graphite
render API format, which the front-end JavaScript still consumes).

Series definitions come from settings:

- INST_SERIES / CORES_SERIES: [(alias, [az, ...]), ...] naming each
  chart series and the availability zones summed into it.
- COMPOSITION_AZ_GROUPS: {tab_key: [az, ...] or None} where None
  means all availability zones.
"""

from datetime import datetime
import re
import time
from urllib.parse import urlencode
import zoneinfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings

# Matches the values accepted by the views' _safe_window /
# _safe_summarise sanitisers.
_RELATIVE_RE = re.compile(
    r'^-?(?P<num>\d+)(?P<unit>s|seconds?|min|minutes?|h|hours?|d|days?'
    r'|w|weeks?|mon|months?|y|years?)$'
)
_ABSOLUTE_RE = re.compile(r'^(\d{4})(\d{2})(\d{2})$')  # yyyymmdd

# Time unit sizes for the URL time expressions (months are 30 days,
# years 365 -- inherited from Graphite, which defined this grammar).
_UNIT_SECONDS = {
    's': 1,
    'min': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
    'mon': 2592000,
    'y': 31536000,
}

DEFAULT_STEP = 1800  # the collectors run every 30 minutes


def _build_session():
    """Reusable session with a retry-on-5xx adapter."""
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_SESSION = _build_session()


def _unit_seconds(unit):
    if unit.startswith('mon'):
        return _UNIT_SECONDS['mon']
    if unit.startswith('min'):
        return _UNIT_SECONDS['min']
    return _UNIT_SECONDS[unit[0]]


def window_seconds(value):
    """Length in seconds of a relative window/summarise expression
    like -6months, 1days or 12hours."""
    match = _RELATIVE_RE.match(value)
    if not match:
        raise ValueError(f"Unparseable time expression {value!r}")
    return int(match.group('num')) * _unit_seconds(match.group('unit'))


def parse_time(value, now=None):
    """Convert a from/until time expression to a unix timestamp.

    Relative expressions (-6months) are offsets from now; absolute
    yyyymmdd dates are midnight in the Django timezone.
    """
    now = now or int(time.time())
    if value is None:
        return now
    match = _ABSOLUTE_RE.match(value)
    if match:
        tzinfo = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        date = datetime(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            tzinfo=tzinfo,
        )
        return int(date.timestamp())
    return now - window_seconds(value)


def _get(path, params):
    url = "{}{}?{}".format(
        settings.VICTORIAMETRICS_URL.rstrip('/'), path, urlencode(params)
    )
    response = _SESSION.get(url, timeout=(5, 30))
    response.raise_for_status()
    payload = response.json()
    if payload.get('status') != 'success':
        raise ValueError(
            "VictoriaMetrics query failed: {}".format(
                payload.get('error', 'unknown error')
            )
        )
    return payload['data']['result']


def query_range(query, start, end, step):
    return _get(
        '/api/v1/query_range',
        [
            ('query', query),
            ('start', int(start)),
            ('end', int(end)),
            ('step', int(step)),
        ],
    )


def query_instant(query, at):
    return _get('/api/v1/query', [('query', query), ('time', int(at))])


def _shift_timestamps(result_values, step):
    """Relabel window-ending evaluation timestamps as bucket starts."""
    return [[float(ts) - step, value] for ts, value in result_values]


def _grid_datapoints(result_values, start, end, step):
    """Re-grid a Prometheus matrix onto the full start..end step grid
    with nulls for missing points, in the front-end's datapoint order
    ([value, timestamp])."""
    values = dict(
        (int(float(ts)), float(value)) for ts, value in result_values
    )
    return [
        [values.get(ts), ts]
        for ts in range(int(start), int(end) + 1, int(step))
    ]


def _az_selector(azs):
    """Regex alternation matching the given availability zones,
    escaped for embedding in a double-quoted PromQL string literal:
    backslashes introduced by re.escape are doubled, because the
    string literal layer consumes one level of escaping (a bare
    \\- is an invalid escape sequence and VictoriaMetrics rejects
    the whole query with a 422).

    None or an empty list selects all availability zones. The empty
    list spelling exists because Helm 3 drops map keys whose override
    value is null, so chart values cannot reliably deliver None.
    """
    if not azs:
        return '.+'
    regex = '|'.join(re.escape(az) for az in azs)
    return regex.replace('\\', '\\\\').replace('"', '\\"')


def aggregate_series(
    metric, series, from_date=None, until_date=None, summarise=None, now=None
):
    """Range data for the growth charts.

    For each (alias, azs) pair, sums the per-bucket averages of the
    metric across the availability zones.
    """
    now = now or int(time.time())
    start = parse_time(from_date, now)
    end = parse_time(until_date, now)
    step = window_seconds(summarise) if summarise else DEFAULT_STEP
    if step == 0:
        raise ValueError(f"Zero-length summarise step {summarise!r}")
    # VictoriaMetrics aligns query_range start/end (and therefore the
    # returned timestamps) to multiples of step; align the grid the
    # same way or every timestamp lookup misses.
    start -= start % step
    end -= end % step

    data = []
    for alias, azs in series:
        # offset 1s turns the (T, T+step] rollup window into
        # [T, T+step) membership - same closed-open buckets as
        # Graphite's summarize, so slot-aligned datapoints land in the
        # same bucket on both backends.
        query = (
            f'sum(avg_over_time({metric}{{az=~"{_az_selector(azs)}"}}'
            f'[{step}s] offset 1s))'
        )
        # xxx_over_time at timestamp T covers the window ENDING at T,
        # while Graphite's summarize labels buckets by their START.
        # Query one step ahead and relabel, so the bucket covering
        # [T, T+step) is emitted at T like summarize did.
        result = query_range(query, start + step, end + step, step)
        values = _shift_timestamps(result[0]['values'] if result else [], step)
        data.append(
            {
                'target': alias,
                'datapoints': _grid_datapoints(values, start, end, step),
            }
        )
    return data


def composition_values(name, azs, now=None):
    """Latest per-group used_vcpus composition, summed across the
    given availability zones.

    Returns [{"target": group, "value": total}, ...] sorted by value.
    """
    now = now or int(time.time())
    if name == 'domain':
        metric, label = 'nectar_domain_used_vcpus', 'domain'
    elif name == 'allocation_home':
        metric, label = 'nectar_allocation_home_used_vcpus', 'home'
    else:
        # Unknown composition names have no data.
        return []
    query = f'sum by ({label}) (last_over_time({metric}{{az=~"{_az_selector(azs)}"}}[1h]))'
    result = query_instant(query, now)
    cleaned = [
        {
            'target': item['metric'].get(label, 'unknown'),
            'value': float(item['value'][1]),
        }
        for item in result
    ]
    cleaned.sort(key=lambda x: x['value'])
    return cleaned


def user_statistics_series(from_date, until_date=None, now=None):
    """Daily cumulative and per-day user registration counts - the
    equivalent of smartSummarize(users.total, "1d", "max") and its
    derivative()."""
    now = now or int(time.time())
    start = parse_time(from_date, now)
    end = parse_time(until_date, now)
    step = 86400
    # Align to the VictoriaMetrics query_range grid (see
    # aggregate_series).
    start -= start % step
    end -= end % step

    # Same bucket-start relabelling and closed-open bucket membership
    # (offset 1s) as aggregate_series.
    result = query_range(
        'max_over_time(nectar_users_total[1d] offset 1s)',
        start + step,
        end + step,
        step,
    )
    values = _shift_timestamps(result[0]['values'] if result else [], step)
    cumulative = _grid_datapoints(values, start, end, step)

    # Graphite's derivative(): difference between consecutive points,
    # None when either side is missing (a gap also blanks the point
    # immediately after it, matching graphite exactly).
    frequency = []
    previous = None
    for value, ts in cumulative:
        if previous is None or value is None:
            frequency.append([None, ts])
        else:
            frequency.append([value - previous, ts])
        previous = value

    return [
        {'target': 'Cumulative', 'datapoints': cumulative},
        {'target': 'Frequency', 'datapoints': frequency},
    ]
