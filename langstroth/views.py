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
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render

SERVICE_NAMES = {'http_cinder-api': 'Cinder',
                 'https': 'Dashboard',
                 'http_glance-registry': 'Glance',
                 'http_keystone-adm': 'Keystone (Admin)',
                 'http_keystone-pub': 'Keystone',
                 'http_ec2': 'Nova (EC2)',
                 'http_nova-api': "Nova"}

GRAPHITE = settings.GRAPHITE_URL + "/render/"


def index(request):
    now = datetime.datetime.now()
    then = now - relativedelta(months=6)
    url = settings.NAGIOS_AVAILABILITY % (calendar.timegm(then.utctimetuple()),
                                          calendar.timegm(now.utctimetuple()))
    url = settings.NAGIOS_URL + url
    print url
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    tr = cssselect.GenericTranslator()
    h = lxml.etree.HTML(resp.text)
    table = None
    for i, e in enumerate(h.xpath(tr.css_to_xpath('.dataTitle')), -1):
        if settings.NAGIOS_SERVICE_GROUP not in e.text:
            continue
        if 'Service State Breakdowns' not in e.text:
            continue
        table = h.xpath(tr.css_to_xpath('table.data'))[i]
        break
    services = []
    average = {}
    if table is not None:
        for row in table.xpath(tr.css_to_xpath("tr.dataOdd, tr.dataEven")):
            if 'colspan' in row.getchildren()[0].attrib:
                title, ok, warn, unknown, crit, undet = row.getchildren()
                average = {"name": "Average",
                           "ok": ok.text.split(' ')[0],
                           "warning": warn.text.split(' ')[0],
                           "unknown": unknown.text.split(' ')[0],
                           "critical": crit.text.split(' ')[0]}
                continue
            host, service, ok, warn, unknown, crit, undet = row.getchildren()
            service_name = SERVICE_NAMES["".join([t for t in
                                                  service.itertext()])]
            services.append({"name": service_name,
                             "ok": ok.text.split(' ')[0],
                             "warning": warn.text.split(' ')[0],
                             "unknown": unknown.text.split(' ')[0],
                             "critical": crit.text.split(' ')[0]})

    report_range = h.xpath(tr.css_to_xpath('.reportRange'))[0].text
    context = {
        "title": "Service Availability",
        "tagline": "",
        "report_range": report_range,
        "services": services,
        "average": average}

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

INST_TARGETS = {
    'ERSA': "sa.total_instances",
    'QCIF': "qld.total_instances",
    'Monash University': "monash-01.total_instances",
    'Melbourne University': "sumSeries(melbourne-qh2.total_instances,melbourne-np.total_instances)"}


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")
    q_format = request.GET.get('format', 'svg')
    q_summarise = request.GET.get('summarise', None)

    arguments = [('format', q_format),
                 ("from", q_from)]

    for alias, target in INST_TARGETS.items():
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


CORES_TARGETS = {
    'ERSA': "sa.used_vcpus",
    'QCIF': "qld.used_vcpus",
    'Monash University': "monash-01.used_vcpus",
    'Melbourne University': "sumSeries(melbourne-qh2.used_vcpus,melbourne-np.used_vcpus)"}


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    q_format = request.GET.get('format', 'svg')
    q_summarise = request.GET.get('summarise', None)

    arguments = [('format', q_format),
                 ("from", q_from)]

    for alias, target in CORES_TARGETS.items():
        if q_summarise:
            target = 'smartSummarize(%s, "%s", "avg")' % (target, q_summarise)
        target = 'alias(%s, "%s")' % (target, alias)
        arguments.append('target', target)

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
    'melbourne': [("target", "melbourne-qh2.domains.*.used_vcpus"),
                  ("target", "melbourne-np.domains.*.used_vcpus")],
    'all': [("target", "melbourne-qh2.domains.*.used_vcpus"),
            ("target", "melbourne-np.domains.*.used_vcpus"),
            ("target", "monash-01.domains.*.used_vcpus"),
            ("target", "sa.domains.*.used_vcpus"),
            ("target", "qld.domains.*.used_vcpus")]
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
        arguments.append(("target", "%s.domains.*.used_vcpus" % q_az))
    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
    cleaned = defaultdict(dict)
    for domain in req.json():
        domain_name = '.'.join(domain['target'].split('.')[-2].split('_'))
        data = cleaned[domain_name]
        data['target'] = domain_name
        count = choose_first(domain['datapoints']).next()
        if data.get('value'):
            data['value'] += count
        else:
            data['value'] = count
    cleaned = cleaned.values()
    cleaned.sort(key=itemgetter('value'))
    return HttpResponse(dumps(cleaned), req.headers['content-type'])
