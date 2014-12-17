import datetime
from json import dumps
from operator import itemgetter
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.core.cache import cache

from langstroth import nagios
from langstroth import graphite

LOG = logging.getLogger(__name__)


def round_to_day(datetime_object):
    return datetime.datetime(datetime_object.year,
                             datetime_object.month,
                             datetime_object.day)


def index(request):
    now = datetime.datetime.now()
    then = round_to_day(now) - relativedelta(months=6)

    try:
        # Only refresh every 10 min, and keep a backup in case of
        # nagios error.
        availability = (cache.get('_nagios_availability')
                        or nagios.get_availability(then, now))
        cache.set('nagios_availability', availability)
        cache.set('_nagios_availability', availability, 600)
    except:
        availability = cache.get('nagios_availability')

    LOG.debug("Availability: " + str(availability))

    try:
        status = nagios.get_status()
        cache.set('nagios_status', status)
    except:
        status = cache.get('nagios_status')

    LOG.debug("Status: " + str(status))

    context = {"title": "National Endpoint Status",
               "tagline": "",
               "report_range": "%s to Now" % then.strftime('%d, %b %Y')}

    if availability:
        context['average'] = availability['average']
        for host in status['hosts'].values():
            for service in host['services']:
                service['availability'] = \
                    availability['services'][service['name']]

    if status:
        context['hosts'] = sorted(status['hosts'].values(),
                                  key=itemgetter('hostname'))
    else:
        context['hosts'] = []

    if not status or not availability:
        return render(request, "index.html", context, status=503)
    return render(request, "index.html", context)


def growth(request):
    context = {
        "title": "Infrastructure Growth",
        "tagline": "Over the last 6 months."}
    return render(request, "growth.html", context)


def domain(request):
    context = {
        "title": "By domain",
        "tagline": ""}
    return render(request, "domain.html", context)


INST_TARGETS = [
    ('Melbourne University',
     "sumSeries(az.melbourne-qh2.total_instances,"
     "az.melbourne-np.total_instances)"),
    ('Monash University',
     "sumSeries(az.monash-01.total_instances,"
     "az.monash-02.total_instances)"),
    ('QCIF',
     "sumSeries(az.qld.total_instances,"
     "az.QRIScloud.total_instances)"),
    ('ERSA', "az.sa.total_instances"),
    ('NCI', "az.NCI.total_instances"),
    ('Tasmania', "az.tasmania.total_instances"),
    ('Pawsey', "az.pawsey-01.total_instances"),
    ('Intersect', "az.intersect-01.total_instances"),
]


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in INST_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json())
    return HttpResponse(dumps(data), req.headers['content-type'])


CORES_TARGETS = [
    ('Melbourne University',
     "sumSeries(az.melbourne-qh2.used_vcpus,az.melbourne-np.used_vcpus)"),
    ('Monash University',
     "sumSeries(az.monash-01.used_vcpus,az.monash-02.used_vcpus)"),
    ('QCIF',
     "sumSeries(az.qld.used_vcpus,az.QRIScloud.used_vcpus)"),
    ('ERSA', "az.sa.used_vcpus"),
    ('NCI', "az.NCI.used_vcpus"),
    ('Tasmania', "az.tasmania.used_vcpus"),
    ('Pawsey', "az.pawsey-01.used_vcpus"),
    ('Intersect', "az.intersect-01.used_vcpus"),
]


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    q_summarise = request.GET.get('summarise', None)

    targets = [graphite.Target(target).summarize(q_summarise).alias(alias)
               for alias, target in CORES_TARGETS]

    req = graphite.get(from_date=q_from, targets=targets)
    data = graphite.fill_null_datapoints(req.json())
    return HttpResponse(dumps(data), req.headers['content-type'])


def choose_first(datapoints):
    for value, time in datapoints:
        if value:
            yield value


QUERY = {
    'melbourne': ["az.melbourne-qh2.domain.*.used_vcpus",
                  "az.melbourne-np.domain.*.used_vcpus"],
    'qld': ["az.qld.domain.*.used_vcpus",
            "az.QRIScloud.domain.*.used_vcpus"],
    'monash': ["az.monash-01.domain.*.used_vcpus",
               "az.monash-02.domain.*.used_vcpus"],
    'pawsey': ["az.pawsey-01.domain.*.used_vcpus"],
    'intersect': ["az.intersect-01.domain.*.used_vcpus"],
    'all': ["az.melbourne-qh2.domain.*.used_vcpus",
            "az.melbourne-np.domain.*.used_vcpus",
            "az.monash-01.domain.*.used_vcpus",
            "az.monash-02.domain.*.used_vcpus",
            "az.NCI.domain.*.used_vcpus",
            "az.sa.domain.*.used_vcpus",
            "az.qld.domain.*.used_vcpus",
            "az.QRIScloud.domain.*.used_vcpus",
            "az.tasmania.domain.*.used_vcpus",
            "az.intersect-01.domain.*.used_vcpus",
            "az.pawsey-01.domain.*.used_vcpus"]
}


def total_cores_per_domain(request):
    q_from = request.GET.get('from', "-60minutes")
    q_az = request.GET.get('az', "melbourne")
    targets = []

    if q_az in QUERY:
        targets.extend([graphite.Target(target)
                        for target in QUERY[q_az]])
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
