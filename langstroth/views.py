import calendar
import datetime
import requests
import cssselect
import lxml.etree
from json import dumps
from operator import itemgetter
from urllib import urlencode
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse, HttpResponseServerError
from django.conf import settings
from django.shortcuts import render
from django.core.cache import cache


from langstroth import nagios

GRAPHITE = settings.GRAPHITE_URL + "/render/"


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

    try:
        status = nagios.get_status()
        cache.set('nagios_status', status)
    except:
        status = cache.get('nagios_status')

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
        return render(request, "index.html", context, status=500)
    return render(request, "index.html", context)


def growth(request):
    context = {
        "title": "Cloud Growth",
        "tagline": ""}
    return render(request, "growth.html", context)


def domain(request):
    context = {
        "title": "By domain",
        "tagline": ""}
    return render(request, "domain.html", context)

INST_TARGETS = [
    ('Melbourne University', "sumSeries(cells.melbourne-qh2.total_instances,cells.melbourne-np.total_instances)"),
    ('Monash University', "cells.monash-01.total_instances"),
    ('QCIF', "cells.qld.total_instances"),
    ('ERSA', "cells.sa.total_instances"),
    ('NCI', "cells.NCI.total_instances"),
    ('Tasmania', "cells.tasmania.total_instances"),
]


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")
    q_format = request.GET.get('format', 'svg')
    q_summarise = request.GET.get('summarise', None)

    arguments = [('format', q_format),
                 ("from", q_from)]

    for alias, target in INST_TARGETS:
        if q_summarise:
            target = 'smartSummarize(%s, "%s", "avg")' % (target, q_summarise)
        target = 'alias(%s, "%s")' % (target, alias)
        arguments.append(('target', target))

    if q_format != 'json':
        arguments.extend(
            [("width", 555),
             ("height", 400),
             ("lineMode", "connected"),
             ("vtitle", "Instances"),
             ("areaMode", "stacked"),
             ("template", "tango"),
             ("title", "Total Instances")])

    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
    return HttpResponse(req, req.headers['content-type'])


CORES_TARGETS = [
    ('Melbourne University', "sumSeries(cells.melbourne-qh2.used_vcpus,cells.melbourne-np.used_vcpus)"),
    ('Monash University', "cells.monash-01.used_vcpus"),
    ('QCIF', "cells.qld.used_vcpus"),
    ('ERSA', "cells.sa.used_vcpus"),
    ('NCI', "cells.NCI.used_vcpus"),
    ('Tasmania', "cells.tasmania.used_vcpus"),
]


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    q_format = request.GET.get('format', 'svg')
    q_summarise = request.GET.get('summarise', None)

    arguments = [('format', q_format),
                 ("from", q_from)]

    for alias, target in CORES_TARGETS:
        if q_summarise:
            target = 'smartSummarize(%s, "%s", "avg")' % (target, q_summarise)
        target = 'alias(%s, "%s")' % (target, alias)
        arguments.append(('target', target))

    if q_format != 'json':
        arguments.extend(
            [("width", 555),
             ("height", 400),
             ("lineMode", "connected"),
             ("vtitle", "VCPU's"),
             ("areaMode", "stacked"),
             ("template", "tango"),
             ("title", "Used VCPU's")])

    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
    return HttpResponse(req, req.headers['content-type'])


def choose_first(datapoints):
    for value, time in datapoints:
        if value:
            yield value


QUERY = {
    'melbourne': [("target", "cells.melbourne-qh2.domains.*.used_vcpus"),
                  ("target", "cells.melbourne-np.domains.*.used_vcpus")],
    'all': [("target", "cells.melbourne-qh2.domains.*.used_vcpus"),
            ("target", "cells.melbourne-np.domains.*.used_vcpus"),
            ("target", "cells.monash-01.domains.*.used_vcpus"),
            ("target", "cells.NCI.domains.*.used_vcpus"),
            ("target", "cells.sa.domains.*.used_vcpus"),
            ("target", "cells.qld.domains.*.used_vcpus"),
            ("target", "cells.tasmania.domains.*.used_vcpus")]
}


def total_cores_per_domain(request):
    q_from = request.GET.get('from', "-60minutes")
    q_az = request.GET.get('az', "melbourne")
    arguments = [('format', 'json'),
                 ("from", q_from),
                 ]
    if q_az in QUERY:
        arguments.extend(QUERY[q_az])
    else:
        arguments.append(("target", "cells.%s.domains.*.used_vcpus" % q_az))
    print GRAPHITE + "?" + urlencode(arguments)
    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
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
