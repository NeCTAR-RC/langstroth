import calendar
import datetime
import requests
import cssselect
import lxml.etree
from urllib import urlencode
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


def total_instance_count(request):
    q_from = request.GET.get('from', "-6months")

    arguments = [("width", 555),
                 ("height", 400),
                 ("lineMode", "connected"),
                 ("from", q_from),
                 ("vtitle", "Instances"),
                 ("template", "solarized-white"),
                 ("title", "Total Instances"),
                 ("target", "total_instances"),
                 ("target", "*.total_instances"),
    ]
    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
    return HttpResponse(req, req.headers['content-type'])


def total_used_cores(request):
    q_from = request.GET.get('from', "-6months")
    arguments = [("width", 555),
                 ("height", 400),
                 ("lineMode", "connected"),
                 ("from", q_from),
                 ("vtitle", "VCPU's"),
                 ("template", "solarized-white"),
                 ("title", "Used VCPU's"),
                 ("target", "used_vcpus"),
                 ("target", "*.used_vcpus"),
    ]
    req = requests.get(GRAPHITE + "?" + urlencode(arguments))
    return HttpResponse(req, req.headers['content-type'])
