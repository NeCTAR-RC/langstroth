import calendar
import requests
import cssselect
import lxml.etree
from django.conf import settings


SERVICE_NAMES = {'http_cinder-api': 'Cinder',
                 'https': 'Dashboard',
                 'http_glance-registry': 'Glance (Registry)',
                 'http_keystone-adm': 'Keystone (Admin)',
                 'http_keystone-pub': 'Keystone',
                 'http_ec2': 'Nova (EC2)',
                 'http_nova-api': "Nova",
                 'http_heat-api': "Heat",
                 'http_glance-api': "Glance",
                 'http_designate-api': "Designate"}


def parse_availability(html):
    tr = cssselect.GenericTranslator()
    h = lxml.etree.HTML(html)
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
            nagios_service_name = "".join([t for t in service.itertext()])
            if nagios_service_name not in SERVICE_NAMES:
                continue
            service_name = SERVICE_NAMES[nagios_service_name]
            services.append({"name": service_name,
                             "ok": ok.text.split(' ')[0],
                             "warning": warn.text.split(' ')[0],
                             "unknown": unknown.text.split(' ')[0],
                             "critical": crit.text.split(' ')[0]})

    report_range = h.xpath(tr.css_to_xpath('.reportRange'))[0].text
    context = {
        "report_range": report_range,
        "services": services,
        "average": average}
    return context


def gm_timestamp(datetime_object):
    return calendar.timegm(datetime_object.utctimetuple())


def get_availability(start_date, end_date):
    url = settings.NAGIOS_AVAILABILITY % (gm_timestamp(start_date),
                                          gm_timestamp(end_date))
    url = settings.NAGIOS_URL + url
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    return parse_availability(resp.text)
