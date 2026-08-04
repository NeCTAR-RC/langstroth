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
import lxml.etree
import requests

from langstroth import metrics
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
    # Per-window primary cache key: scoped to the requested window so
    # different report ranges don't collide. Short TTL because Nagios
    # data ages quickly.
    primary_key = (
        f'nagios_availability_{service_group}_{now.date()}_{then.date()}'
    )
    # Stable backup key: NO date in the key, long TTL. Purpose is to
    # serve *something* if Nagios is unreachable. May be from a
    # slightly different report window than the user requested -- a
    # reasonable trade for not going dark when Nagios is down.
    backup_key = f'nagios_availability_backup_{service_group}'
    # Narrow except: Nagios down (RequestException), template/page
    # layout drift (Value/Index/Attribute/KeyError, LxmlError). A bare
    # `except Exception` here masks programming errors and silently
    # serves stale cache forever.
    _SCRAPE_ERRORS = (
        requests.RequestException,
        ValueError,
        IndexError,
        AttributeError,
        KeyError,
        lxml.etree.LxmlError,
    )

    try:
        availability = cache.get(primary_key)
        if not availability:
            availability = get_availability(then, now, service_group)
            cache.set(primary_key, availability, 600)
            cache.set(backup_key, availability, 24 * 3600)
    except _SCRAPE_ERRORS as ex:
        LOG.warning("Problem getting availability info", exc_info=ex)
        availability = cache.get(backup_key)

    LOG.debug("Availability: " + str(availability))

    try:
        # Refresh every minute, and don't keep a backup
        status = cache.get(f'nagios_status_{service_group}')
        if not status:
            status = get_status(service_group)
            cache.set(f'nagios_status_{service_group}', status, 60)
    except _SCRAPE_ERRORS as ex:
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
                    LOG.warning(
                        "Nagios inconsistency: no availability info "
                        "for service '" + name + "'"
                    )
                    # No data -- template renders "n/a" rather than 0.00%
                    # which would falsely imply we measured the service
                    # and got zero.
                    service['availability'] = {
                        'name': name,
                        'ok': None,
                        'critical': None,
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
            "project trials. "
            "In some cases, a project might be categorised as national, "
            "but does not necessarily meet the requirements, so these "
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


# Allowed time-window expressions for the from= / until= / summarise=
# query parameters. Restricting these keeps arbitrary text out of the
# queries the metrics backend builds by string interpolation.
_RELATIVE_RE = re.compile(
    r'^-?\d+(?:s|seconds?|min|minutes?|h|hours?|d|days?|w|weeks?|mon|months?|y|years?)$'
)
_ABSOLUTE_RE = re.compile(r'^\d{8}$')  # yyyymmdd
_SUMMARISE_RE = re.compile(
    r'^\d+(?:s|seconds?|min|minutes?|h|hours?|d|days?|w|weeks?|mon|months?|y|years?)$'
)


def _safe_window(value, default=None):
    """Return value if it is a recognised relative-or-absolute time
    expression; else default."""
    if value is None:
        return default
    if _RELATIVE_RE.match(value) or _ABSOLUTE_RE.match(value):
        return value
    return default


def _safe_summarise(value):
    if value is None:
        return None
    if _SUMMARISE_RE.match(value):
        return value
    return None


def _safe_token(value, default='all'):
    """Allow only alphanumeric / underscore / dash so the value cannot
    inject extra query expressions."""
    if value is None:
        return default
    if re.match(r'^[A-Za-z0-9_-]+$', value):
        return value
    return default


def _metrics_unavailable():
    return HttpResponse(dumps([]), content_type='application/json', status=503)


def _growth_series(metric, series, q_from, q_until, q_summarise):
    """Growth chart data in the null-filled JSON shape the front-end
    charts consume."""
    try:
        data = metrics.aggregate_series(
            metric,
            series,
            from_date=q_from,
            until_date=q_until,
            summarise=q_summarise,
        )
        data = metrics.fill_null_datapoints(data, q_summarise)
    except (requests.RequestException, ValueError, IndexError) as ex:
        LOG.warning(
            "Problem fetching %s from the metrics backend",
            metric,
            exc_info=ex,
        )
        return _metrics_unavailable()
    return HttpResponse(dumps(data), content_type='application/json')


def total_instance_count(request):
    q_from = _safe_window(request.GET.get('from'), "-6months")
    q_until = _safe_window(request.GET.get('until'))
    q_summarise = _safe_summarise(request.GET.get('summarise'))

    return _growth_series(
        'nectar_total_instances',
        settings.INST_SERIES,
        q_from,
        q_until,
        q_summarise,
    )


def total_used_cores(request):
    q_from = _safe_window(request.GET.get('from'), "-6months")
    q_until = _safe_window(request.GET.get('until'))
    q_summarise = _safe_summarise(request.GET.get('summarise'))

    return _growth_series(
        'nectar_used_vcpus',
        settings.CORES_SERIES,
        q_from,
        q_until,
        q_summarise,
    )


def composition_cores(request, name):
    q_az = _safe_token(request.GET.get('az'), "all")

    if q_az in settings.COMPOSITION_AZ_GROUPS:
        azs = settings.COMPOSITION_AZ_GROUPS[q_az]
    else:
        azs = [q_az]
    try:
        cleaned = metrics.composition_values(name, azs)
    except (requests.RequestException, ValueError) as ex:
        LOG.warning(
            "Problem fetching composition from the metrics backend",
            exc_info=ex,
        )
        return _metrics_unavailable()
    return HttpResponse(dumps(cleaned), content_type='application/json')
