import datetime
from json import dumps
from operator import itemgetter
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import logging
import re

from django.http import HttpResponse
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from django.template.defaultfilters import pluralize

from langstroth import nagios
from langstroth import graphite

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
        availability = (cache.get("_%s" % cache_key)
                        or nagios.get_availability(then, now, service_group))
        cache.set(cache_key, availability)
        cache.set("_%s" % cache_key, availability, 600)
    except:
        availability = cache.get(cache_key)

    LOG.debug("Availability: " + str(availability))

    try:
        status = nagios.get_status(service_group)
        cache.set('nagios_status_%s' % service_group, status)
    except:
        status = cache.get('nagios_status_%s' % service_group)

    LOG.debug("Status: " + str(status))

    if availability:
        context['%s_average' % service_group_type] = availability['average']
        for host in status['hosts'].values():
            for service in host['services']:
                service['availability'] = \
                    availability['services'][service['name']]

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

    if error:
        return render(request, "index.html", context, status=503)
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


def capacity(request):
    context = {
        "title": "Capacity",
        "tagline": "Over the last 6 months.",
        'ram_sizes': [768, 2048, 4096, 6144, 8192,
                      12288, 16384, 32768, 49152, 65536]
    }
    return render(request, "capacity.html", context)


def domain(request):
    context = {
        "title": "By domain",
        "tagline": ""}
    return render(request, "domain.html", context)


def allocation_home(request):
    context = {
        "title": "By allocation home",
        "tagline": ""}
    return render(request, "allocation_home.html", context)


FAULTS_TARGETS = [
    ('Melbourne University',
     "sumSeries(az.melbourne-qh2.instance_faults,"
     "az.melbourne-np.instance_faults)"),
    ('Monash University',
     "sumSeries(az.monash-01.instance_faults,"
     "az.monash-02.instance_faults)"),
    ('QCIF',
     "sumSeries(az.qld.instance_faults,"
     "az.QRIScloud.instance_faults)"),
    ('ERSA', "az.sa.instance_faults"),
    ('NCI', "az.NCI.instance_faults"),
    ('Tasmania', "az.tasmania.instance_faults"),
    ('Intersect',
     "sumSeries(az.intersect-01.instance_faults,"
     "az.intersect-02.instance_faults)"),
]


def total_faults(request):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in FAULTS_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)
    return HttpResponse(dumps(data), req.headers['content-type'])


INST_TARGETS = [
    ('Melbourne University',
     "sumSeries(az.melbourne-qh2.total_instances,"
     "az.melbourne-qh2-uom.total_instances,"
     "az.melbourne-np.total_instances)"),
    ('Monash University',
     "sumSeries(az.monash-01.total_instances,"
     "az.monash-02.total_instances,"
     "az.monash-03.total_instances)"),
    ('QCIF',
     "sumSeries(az.qld.total_instances,"
     "az.QRIScloud.total_instances)"),
    ('ERSA', "az.sa.total_instances"),
    ('NCI', "az.NCI.total_instances"),
    ('Tasmania', "az.tasmania.total_instances"),
    ('Pawsey', "az.pawsey-01.total_instances"),
    ('Intersect',
     "sumSeries(az.intersect-01.total_instances,"
     "az.intersect-02.total_instances)"),
    ('Swinburne', "az.swinburne-01.total_instances"),
    ('Auckland', "az.auckland.total_instances"),
]


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in INST_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)
    return HttpResponse(dumps(data), req.headers['content-type'])


CORES_TARGETS = [
    ('Melbourne University',
     "sumSeries(az.melbourne-qh2.used_vcpus,"
     "az.melbourne-np.used_vcpus,"
     "az.melbourne-qh2-uom.used_vcpus)"),
    ('Monash University',
     "sumSeries(az.monash-01.used_vcpus,"
     "az.monash-02.used_vcpus,"
     "az.monash-03.used_vcpus)"),
    ('QCIF',
     "sumSeries(az.qld.used_vcpus,az.QRIScloud.used_vcpus)"),
    ('ERSA', "az.sa.used_vcpus"),
    ('NCI', "az.NCI.used_vcpus"),
    ('Tasmania', "az.tasmania.used_vcpus"),
    ('Pawsey', "az.pawsey-01.used_vcpus"),
    ('Intersect',
     "sumSeries(az.intersect-01.used_vcpus,"
     "az.intersect-02.used_vcpus)"),
    ('Swinburne', "az.swinburne-01.used_vcpus"),
    ('Auckland', "az.auckland.used_vcpus"),
]


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in CORES_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)
    return HttpResponse(dumps(data), req.headers['content-type'])


CAPACITY_TARGETS = [
    ('Melbourne University',
     "sumSeries(cell.qh2.capacity_%(ram_size)s,"
     "cell.np.capacity_%(ram_size)s,"
     "cell.melbourne.capacity_%(ram_size)s)"),
    ('Monash University',
     "sumSeries(cell.monash-01.capacity_%(ram_size)s,"
     "cell.monash-02.capacity_%(ram_size)s,"
     "cell.monash.capacity_%(ram_size)s)"),
    ('Monash University', "cell.monash.capacity_%(ram_size)s"),
    ('QCIF', "cell.qld-upstart.capacity_%(ram_size)s"),
    ('ERSA', "cell.sa-cw.capacity_%(ram_size)s"),
    ('NCI', "cell.NCI.capacity_%(ram_size)s"),
    ('Tasmania',
     "sumSeries(cell.tas-m.capacity_%(ram_size)s,"
     "cell.tas-s.capacity_%(ram_size)s,"
     "cell.tas.capacity_%(ram_size)s)"),
    ('Intersect',
     "sumSeries(cell.intersect-01.capacity_%(ram_size)s,"
     "cell.intersect-02.capacity_%(ram_size)s)"),
    ('Swinburne', "cell.sut1.capacity_%(ram_size)s"),
    ('Auckland', "cell.auckland.capacity_%(ram_size)s"),
]


def total_capacity(request, ram_size=4096):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(
        target % {'ram_size': ram_size}).summarize(q_summarise).alias(alias)
        for alias, target in CAPACITY_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json(), q_summarise)

    return HttpResponse(dumps(data), req.headers['content-type'])


def choose_first(datapoints):
    for value, time in datapoints:
        if value:
            yield value


DOMAIN_QUERY = {
    'melbourne': ["az.melbourne-qh2.domain.*.used_vcpus",
                  "az.melbourne-qh2-uom.domain.*.used_vcpus",
                  "az.melbourne-np.domain.*.used_vcpus"],
    'qld': ["az.qld.domain.*.used_vcpus",
            "az.QRIScloud.domain.*.used_vcpus"],
    'monash': ["az.monash-01.domain.*.used_vcpus",
               "az.monash-02.domain.*.used_vcpus",
               "az.monash-03.domain.*.used_vcpus"],
    'swinburne': ["az.swinburne-01.domain.*.used_vcpus"],
    'intersect': ["az.intersect-01.domain.*.used_vcpus",
                  "az.intersect-02.domain.*.used_vcpus"],
    'all': ["az.*.domain.*.used_vcpus"],
}


def total_cores_per_domain(request):
    q_from = request.GET.get('from', "-60minutes")
    q_az = request.GET.get('az', "melbourne")
    targets = []

    if q_az in DOMAIN_QUERY:
        targets.extend([graphite.Target(target)
                        for target in DOMAIN_QUERY[q_az]])
    else:
        targets.append(graphite.Target("az.%s.domain.*.used_vcpus" % q_az))
    req = graphite.get(from_date=q_from, targets=targets)
    cleaned = defaultdict(dict)
    for domain in req.json():
        domain_name = '.'.join(domain['target'].split('.')[-2].split('_'))
        data = cleaned[domain_name]
        data['target'] = domain_name
        try:
            count = choose_first(domain['datapoints']).next()
        except:
            count = 0
        if data.get('value'):
            data['value'] += count
        else:
            data['value'] = count
    cleaned = cleaned.values()
    cleaned.sort(key=itemgetter('value'))
    return HttpResponse(dumps(cleaned), req.headers['content-type'])


HOME_QUERY = {
    'melbourne': ["az.melbourne-qh2.allocation_home.*.used_vcpus",
                  "az.melbourne-qh2-uom.allocation_home.*.used_vcpus",
                  "az.melbourne-np.allocation_home.*.used_vcpus"],
    'qld': ["az.qld.allocation_home.*.used_vcpus",
            "az.QRIScloud.allocation_home.*.used_vcpus"],
    'monash': ["az.monash-01.allocation_home.*.used_vcpus",
               "az.monash-02.allocation_home.*.used_vcpus",
               "az.monash-03.allocation_home.*.used_vcpus"],
    'swinburne': ["az.swinburne-01.allocation_home.*.used_vcpus"],
    'intersect': ["az.intersect-01.allocation_home.*.used_vcpus",
                  "az.intersect-02.allocation_home.*.used_vcpus"],
    'all': ["az.*.allocation_home.*.used_vcpus"],
}


def total_cores_per_allocation_home(request):
    q_from = request.GET.get('from', "-60minutes")
    q_az = request.GET.get('az', "melbourne")
    targets = []

    if q_az in HOME_QUERY:
        targets.extend([graphite.Target(target)
                        for target in HOME_QUERY[q_az]])
    else:
        targets.append(graphite.Target("az.%s.allocation_home.*.used_vcpus" % q_az))
    req = graphite.get(from_date=q_from, targets=targets)
    cleaned = defaultdict(dict)
    for allocation_home in req.json():
        allocation_home_name = '.'.join(allocation_home['target'].split('.')[-2].split('_'))
        data = cleaned[allocation_home_name]
        data['target'] = allocation_home_name
        try:
            count = choose_first(allocation_home['datapoints']).next()
        except:
            count = 0
        if data.get('value'):
            data['value'] += count
        else:
            data['value'] = count
    cleaned = cleaned.values()
    cleaned.sort(key=itemgetter('value'))
    return HttpResponse(dumps(cleaned), req.headers['content-type'])
