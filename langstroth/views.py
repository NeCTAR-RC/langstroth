from collections import defaultdict
import datetime
from dateutil.relativedelta import relativedelta
from json import dumps
import logging
from operator import itemgetter
import re

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import pluralize
from django.utils import timezone
import requests

from langstroth import graphite
from langstroth.nagios import get_availability
from langstroth.nagios import get_status
from langstroth.outages import filters
from langstroth.outages import models

LOG = logging.getLogger(__name__)


def round_to_day(datetime_object):
    return datetime_object.replace(hour=0, minute=0, second=0, microsecond=0)


def _get_hosts(
    context,
    now,
    then,
    service_group=settings.NAGIOS_SERVICE_GROUP,
    service_group_type='api',
):
    cache_key = (
        f'nagios_availability_{service_group}_{now.date()}_{then.date()}'
    )
    try:
        # Only refresh every 10 min, and keep a backup in case of
        # nagios error.
        availability = cache.get(f"_{cache_key}")
        if not availability:
            availability = get_availability(then, now, service_group)
            cache.set(f"_{cache_key}", availability, 600)
            # Save the backup
            cache.set(cache_key, availability)
    except Exception as ex:
        # Could be a Memcached outage, a Nagios outage, a networking
        # outage, fragility in the scraping code, or ...
        LOG.warning("Problem getting availability info", exc_info=ex)
        # Use the backup
        availability = cache.get(cache_key)

    LOG.debug("Availability: " + str(availability))

    try:
        # Refresh every minute, and don't keep a backup
        status = cache.get(f'nagios_status_{service_group}')
        if not status:
            status = get_status(service_group)
            cache.set(f'nagios_status_{service_group}', status, 60)
    except Exception as ex:
        # See above ...
        LOG.warning("Problem getting status info", exc_info=ex)
        status = None

    LOG.debug("Status: " + str(status))

    if availability and status and status['hosts']:
        context[f'{service_group_type}_average'] = availability['average']
        for host in status['hosts'].values():
            for service in host['services']:
                name = service['name']
                try:
                    service['availability'] = availability['services'][name]
                except KeyError:
                    LOG.warn(
                        "Nagios inconsistency: no availability info "
                        "for service '" + name + "'"
                    )
                    service['availability'] = {
                        'name': name,
                        'ok': 0.0,
                        'critical': 0.0,
                    }

    if status:
        context[f'{service_group_type}_hosts'] = sorted(
            status['hosts'].values(), key=itemgetter('hostname')
        )
    else:
        context[f'{service_group_type}_hosts'] = []

    error = False
    if not status or not availability:
        error = True
    return context, error


class SimpleActivityFilter(filters.ActivityFilterMixin):
    def filter(self, queryset, name):
        return self.filter_activity(queryset, "", name)


def _add_outages(context):
    filter = SimpleActivityFilter()
    queryset = models.Outage.objects.all()

    context['active'] = filter.filter(queryset, "active")
    context['completed'] = filter.filter(queryset, "completed")[:3]
    context['upcoming'] = filter.filter(queryset, "upcoming")

    context['current'] = models.Outage.objects.current_outages()


def index(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    now = None
    start_date = None
    end_date = None
    report_range = None
    if end:
        try:
            end_date = timezone.make_aware(
                datetime.datetime.strptime(end, "%Y-%m-%d")
            )
        except ValueError:
            pass

    if not end_date:
        end_date = timezone.now()
        now = 'Now'

    if start:
        if start.startswith('-'):
            try:
                res = re.search(r'^-(?P<value>\d*)(?P<period>\w+)$', start)
                value = int(res.group('value'))
                period = res.group('period')
                args = {period: value}
                start_date = timezone.now() - relativedelta(**args)
                period_str = period.rstrip('s')
                report_range = (
                    f"Over the last {value} {period_str}{pluralize(value)}"
                )
            except Exception:
                pass
        else:
            try:
                start_date = timezone.make_aware(
                    datetime.datetime.strptime(start, "%Y-%m-%d")
                )
            except ValueError:
                pass

    if not start_date:
        start_date = timezone.now() - relativedelta(months=1)
        report_range = "Over the last 1 month"

    start_date = round_to_day(start_date)
    end_date = round_to_day(end_date)

    if not report_range:
        report_range = "{} to {}".format(
            start_date.strftime('%d %b %Y'),
            now or end_date.strftime('%d %b %Y'),
        )

    context = {"title": "Research Cloud Status", "tagline": report_range}

    context, error = _get_hosts(context, end_date, start_date)
    context, error = _get_hosts(
        context,
        end_date,
        start_date,
        service_group='tempest_compute',
        service_group_type='site',
    )

    _add_outages(context)

    warning = 0
    critical = 0
    for hosts in (context['api_hosts'], context['site_hosts']):
        for host in hosts:
            for service in host['services']:
                if service['status'] == 'Critical':
                    critical += 1
                elif service['status'] == 'Warning':
                    warning += 1
    context['overall_status'] = (
        'Critical' if critical > 0 else 'Warning' if warning > 0 else 'OK'
    )

    if error:
        return render(request, "index.html", context, status=503)
    else:
        return render(request, "index.html", context)


def growth(request):
    context = {
        "title": "Infrastructure Usage",
        "tagline": "Over the last 6 months.",
    }
    return render(request, "growth.html", context)


def composition(request, name):
    title = None
    if name == 'domain':
        title = 'Composition by domain'
        desc = (
            "This graph shows a break down of usage by the number of "
            "VCPUs allocated, grouped by the domain of the user who "
            "launched a VM.  As a result this graph isn't a true "
            "representation of the number of VCPU's being used by an "
            "institution, since many allocations have collaborators from "
            "different institutions."
        )
    elif name == 'allocation_home':
        title = 'Composition by allocation home'
        desc = (
            "This graph shows a break down of usage by the number of "
            "VCPUs allocated, grouped by the allocation home. This value "
            "could be national, none or the specified home institution. "
            "The value of none might be for certain internal projects, or "
            "project trials."
            "In some cases, a project might be categorised as national, "
            "but does not necessarily meet the requrements, so these "
            "figures may not be accurate"
        )

    if title:
        context = {
            "title": title,
            "desc": desc,
            "tabs": settings.COMPOSITION_TABS,
        }
        return render(request, "composition.html", context)
    else:
        raise Http404


# Allowed Graphite time-window expressions for the from= / until= /
# summarise= query parameters. Restricting these prevents callers from
# slipping arbitrary Graphite functions into the metric target string
# (which is built by f-string interpolation in graphite.Target).
_GRAPHITE_RELATIVE_RE = re.compile(
    r'^-?\d+(?:s|seconds?|min|minutes?|h|hours?|d|days?|w|weeks?|mon|months?|y|years?)$'
)
_GRAPHITE_ABSOLUTE_RE = re.compile(r'^\d{8}$')  # yyyymmdd
_GRAPHITE_SUMMARISE_RE = re.compile(
    r'^\d+(?:s|seconds?|min|minutes?|h|hours?|d|days?|w|weeks?|mon|months?|y|years?)$'
)


def _safe_graphite_window(value, default=None):
    """Return value if it is a recognised relative-or-absolute Graphite
    time expression; else default. Rejects anything that could break out
    of a Graphite function-call string."""
    if value is None:
        return default
    if _GRAPHITE_RELATIVE_RE.match(value) or _GRAPHITE_ABSOLUTE_RE.match(
        value
    ):
        return value
    return default


def _safe_graphite_summarise(value):
    if value is None:
        return None
    if _GRAPHITE_SUMMARISE_RE.match(value):
        return value
    return None


def _safe_graphite_token(value, default='all'):
    """Allow only alphanumeric / underscore / dash so the value cannot
    close a Graphite function-call string or inject extra expressions."""
    if value is None:
        return default
    if re.match(r'^[A-Za-z0-9_-]+$', value):
        return value
    return default


def _graphite_unavailable():
    return HttpResponse(dumps([]), content_type='application/json', status=503)


def _graphite_json(req):
    """Pull JSON from a Graphite response or raise to the caller.

    Graphite returns text/html with a stack trace on error; raise so the
    caller can surface a 503 instead of leaking the trace into the JSON
    deserialiser.
    """
    req.raise_for_status()
    return req.json()


def total_instance_count(request):
    q_from = _safe_graphite_window(request.GET.get('from'), "-6months")
    q_until = _safe_graphite_window(request.GET.get('until'))
    q_summarise = _safe_graphite_summarise(request.GET.get('summarise'))

    targets = [
        graphite.Target(target).summarize(q_summarise).alias(alias)
        for alias, target in settings.INST_TARGETS
    ]

    try:
        req = graphite.get(
            from_date=q_from, until_date=q_until, targets=targets
        )
        data = graphite.fill_null_datapoints(_graphite_json(req), q_summarise)
    except (requests.RequestException, ValueError, IndexError) as ex:
        LOG.warning(
            "Problem fetching instance count from Graphite", exc_info=ex
        )
        return _graphite_unavailable()
    return HttpResponse(dumps(data), content_type='application/json')


def total_used_cores(request):
    q_from = _safe_graphite_window(request.GET.get('from'), "-6months")
    q_until = _safe_graphite_window(request.GET.get('until'))
    q_summarise = _safe_graphite_summarise(request.GET.get('summarise'))

    targets = [
        graphite.Target(target).summarize(q_summarise).alias(alias)
        for alias, target in settings.CORES_TARGETS
    ]

    try:
        req = graphite.get(
            from_date=q_from, until_date=q_until, targets=targets
        )
        data = graphite.fill_null_datapoints(_graphite_json(req), q_summarise)
    except (requests.RequestException, ValueError, IndexError) as ex:
        LOG.warning("Problem fetching used cores from Graphite", exc_info=ex)
        return _graphite_unavailable()
    return HttpResponse(dumps(data), content_type='application/json')


def choose_first(datapoints):
    for value, time in datapoints:
        if value:
            yield value


def composition_cores(request, name):
    q_from = _safe_graphite_window(request.GET.get('from'), "-60minutes")
    q_az = _safe_graphite_token(request.GET.get('az'), "all")
    targets = []

    if q_az in settings.COMPOSITION_QUERY:
        targets.extend(
            [
                graphite.Target(target % name)
                for target in settings.COMPOSITION_QUERY[q_az]
            ]
        )
    else:
        targets.append(graphite.Target(f"az.{q_az}.{name}.*.used_vcpus"))
    try:
        req = graphite.get(from_date=q_from, targets=targets)
        items = _graphite_json(req)
    except (requests.RequestException, ValueError) as ex:
        LOG.warning("Problem fetching composition from Graphite", exc_info=ex)
        return _graphite_unavailable()
    cleaned = defaultdict(dict)
    for item in items:
        item_name = '.'.join(item['target'].split('.')[-2].split('_'))
        data = cleaned[item_name]
        data['target'] = item_name
        try:
            count = next(choose_first(item['datapoints']))
        except Exception:
            count = 0
        if data.get('value'):
            data['value'] += count
        else:
            data['value'] = count
    cleaned = list(cleaned.values())
    cleaned.sort(key=lambda x: x['value'])
    return HttpResponse(dumps(cleaned), content_type='application/json')
