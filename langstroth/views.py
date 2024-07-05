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

from langstroth import graphite
from langstroth.nagios import get_availability
from langstroth.nagios import get_status
from langstroth.outages import filters
from langstroth.outages import models

LOG = logging.getLogger(__name__)


def round_to_day(datetime_object):
    return datetime.datetime(datetime_object.year,
                             datetime_object.month,
                             datetime_object.day)


def _get_hosts(context, now, then, service_group=settings.NAGIOS_SERVICE_GROUP,
               service_group_type='api'):

    cache_key = 'nagios_availability_%s_%s_%s' % (service_group,
                                                  now.date(), then.date())
    try:
        # Only refresh every 10 min, and keep a backup in case of
        # nagios error.
        availability = cache.get("_%s" % cache_key)
        if not availability:
            availability = get_availability(then, now, service_group)
            cache.set("_%s" % cache_key, availability, 600)
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
        status = cache.get('nagios_status_%s' % service_group)
        if not status:
            status = get_status(service_group)
            cache.set('nagios_status_%s' % service_group, status, 60)
    except Exception as ex:
        # See above ...
        LOG.warning("Problem getting status info", exc_info=ex)
        status = None

    LOG.debug("Status: " + str(status))

    if availability and status and status['hosts']:
        context['%s_average' % service_group_type] = availability['average']
        for host in status['hosts'].values():
            for service in host['services']:
                name = service['name']
                try:
                    service['availability'] = availability['services'][name]
                except KeyError:
                    LOG.warn("Nagios inconsistency: no availability info "
                             "for service '" + name + "'")
                    service['availability'] = {
                        'name': name, 'ok': 0.0, 'critical': 0.0}

    if status:
        context['%s_hosts' % service_group_type] = sorted(
            status['hosts'].values(),
            key=itemgetter('hostname'))
    else:
        context['%s_hosts' % service_group_type] = []

    error = False
    if not status or not availability:
        error = True
    return context, error


class SimpleActivityFilter(filters.ActivityFilterMixin):
    def filter(self, queryset, name):
        return self.filter_activity(queryset, "", name)


def _add_outages(context):
    filter = SimpleActivityFilter()
    queryset = models.Outage.objects.filter(deleted=False)

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
            end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            pass

    if not end_date:
        end_date = datetime.datetime.now()
        now = 'Now'

    if start:
        if start.startswith('-'):
            try:
                res = re.search(r'^-(?P<value>\d*)(?P<period>\w+)$', start)
                value = int(res.group('value'))
                period = res.group('period')
                args = {period: value}
                start_date = datetime.datetime.now() - relativedelta(**args)
                report_range = "Over the last %d %s%s" % (
                    value, period.rstrip('s'), pluralize(value))
            except Exception:
                pass
        else:
            try:
                start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                pass

    if not start_date:
        start_date = datetime.datetime.now() - relativedelta(months=1)
        report_range = "Over the last 1 month"

    start_date = round_to_day(start_date)
    end_date = round_to_day(end_date)

    if not report_range:
        report_range = "%s to %s" % (start_date.strftime('%d %b %Y'),
                                     now or end_date.strftime('%d %b %Y'))

    context = {"title": "Research Cloud Status",
               "tagline": report_range}

    context, error = _get_hosts(context, end_date, start_date)
    context, error = _get_hosts(context, end_date, start_date,
                                service_group='tempest_compute_site',
                                service_group_type='site')

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
    context['overall_status'] = ('Critical' if critical > 0
                                 else 'Warning' if warning > 0
                                 else 'OK')

    if error:
        return render(request, "index.html", context, status=503)
    else:
        return render(request, "index.html", context)


def growth(request):
    context = {
        "title": "Infrastructure Usage",
        "tagline": "Over the last 6 months."}
    return render(request, "growth.html", context)


def faults(request):
    context = {
        "title": "Instance Faults",
        "tagline": "Over the last 6 months."}
    return render(request, "faults.html", context)


def composition(request, name):
    title = None
    if name == 'domain':
        title = 'Composition by domain'
        desc = ("This graph shows a break down of usage by the number of "
                "VCPUs allocated, grouped by the domain of the user who "
                "launched a VM.  As a result this graph isn't a true "
                "representation of the number of VCPU's being used by an "
                "institution, since many allocations have collaborators from "
                "different institutions.")
    elif name == 'allocation_home':
        title = 'Composition by allocation home'
        desc = ("This graph shows a break down of usage by the number of "
                "VCPUs allocated, grouped by the allocation home. This value "
                "could be national, none or the specified home institution. "
                "The value of none might be for certain internal projects, or "
                "project trials."
                "In some cases, a project might be categorised as national, "
                "but does not necessarily meet the requrements, so these "
                "figures may not be accurate")

    if title:
        context = {
            "title": title,
            "desc": desc,
            "tabs": settings.COMPOSITION_TABS,
        }
        return render(request, "composition.html", context)
    else:
        raise Http404


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")
    q_until = request.GET.get('until', None)
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in settings.INST_TARGETS]

    req = graphite.get(from_date=q_from, until_date=q_until, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)
    return HttpResponse(dumps(data), req.headers['content-type'])


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    q_until = request.GET.get('until', None)
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in settings.CORES_TARGETS]

    req = graphite.get(from_date=q_from, until_date=q_until, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)
    return HttpResponse(dumps(data), req.headers['content-type'])


def choose_first(datapoints):
    for value, time in datapoints:
        if value:
            yield value


def composition_cores(request, name):
    q_from = request.GET.get('from', "-60minutes")
    q_az = request.GET.get('az', "all")
    targets = []

    if q_az in settings.COMPOSITION_QUERY:
        targets.extend([graphite.Target(target % name)
                        for target in settings.COMPOSITION_QUERY[q_az]])
    else:
        targets.append(graphite.Target("az.%s.%s.*.used_vcpus" % (q_az, name)))
    req = graphite.get(from_date=q_from, targets=targets)
    cleaned = defaultdict(dict)
    for item in req.json():
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
    sorted(cleaned, key=lambda x: x['value'])
    return HttpResponse(dumps(cleaned),
                        content_type=req.headers['Content-Type'])
