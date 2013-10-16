import calendar
import datetime
import requests
import cssselect
import lxml.etree
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.shortcuts import render

SERVICE_NAMES = {'http_cinder-api': 'Cinder',
                 'https': 'Dashboard',
                 'http_glance-registry': 'Glance',
                 'http_keystone-adm': 'Keystone (Admin)',
                 'http_keystone-pub': 'Keystone',
                 'http_ec2': 'Nova (EC2)',
                 'http_nova-api': "Nova"}


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
        "tagline": "Lead node availability for the last 6 months.",
        "report_range": report_range,
        "services": services,
        "average": average}

    return render(request, "index.html", context)
