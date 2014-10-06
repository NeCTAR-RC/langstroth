import logging
import calendar

import requests
import cssselect
import lxml.etree
from django.conf import settings


LOG = logging.getLogger(__name__)

AVAILABILITY_URL = "avail.cgi?t1=%s&t2=%s&show_log_entries=&servicegroup=%s&assumeinitialstates=yes&assumestateretention=yes&assumestatesduringnotrunning=yes&includesoftstates=yes&initialassumedhoststate=3&initialassumedservicestate=6&timeperiod=[+Current+time+range+]&backtrack=4"
STATUS_URL = "status.cgi?servicegroup=%s&style=detail"

SERVICE_NAMES = {'http_cinder-api': 'Cinder',
                 'https': 'Webserver',
                 'http_ceilometer-api': 'Ceilometer',
                 'http_glance-registry': 'Glance Registry',
                 'http_keystone-adm': 'Keystone Admin',
                 'http_keystone-pub': 'Keystone',
                 'http_ec2': 'EC2',
                 'http_nova-api': "Nova",
                 'http_heat-api': "Heat",
                 'http_glance-api': "Glance",
                 'http_designate-api': "Designate"}


def parse_service_availability(service):
    host, service, ok, warn, unknown, crit, undet = service.getchildren()
    nagios_service_name = "".join([t for t in service.itertext()])
    return {"name": nagios_service_name,
            "ok": ok.text.split(' ')[0],
            "warning": warn.text.split(' ')[0],
            "unknown": unknown.text.split(' ')[0],
            "critical": crit.text.split(' ')[0]}


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
    services = {}
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
            service = parse_service_availability(row)
            services[service['name']] = service

    context = {
        "services": services,
        "average": average}
    return context


def parse_hostlink(hostlink):
    return {'hostname': hostlink.text,
            'services': []}


def parse_service(service_columns):
    tr = cssselect.GenericTranslator()
    name = service_columns[0].xpath(tr.css_to_xpath('a'))[0].text
    return {
        'name': name,
        'display_name': SERVICE_NAMES.get(name),
        'status': service_columns[1].text,
        'last_checked': service_columns[2].text,
        'duration': service_columns[3].text}


def parse_status(html):
    tr = cssselect.GenericTranslator()
    h = lxml.etree.HTML(html)
    table = None
    for i, e in enumerate(h.xpath(tr.css_to_xpath('.statusTitle')), -1):
        if settings.NAGIOS_SERVICE_GROUP not in e.text:
            continue
        if 'Service Status Details' not in e.text:
            continue
        table = h.xpath(tr.css_to_xpath('table.status'))[i]
        break
    hosts = {}
    if table is not None:
        for row in table.getchildren():
            children = row.getchildren()
            # Skip empty rows
            if not len(children) > 1:
                continue
            # Skip header row
            if children[0].tag == 'th':
                continue
            children = row.getchildren()

            hostname = children[0].xpath(tr.css_to_xpath('a'))
            if len(hostname) > 1:
                LOG.warning("Too many links found.")
            elif len(hostname) == 1:
                current_host = parse_hostlink(hostname[0])
                hosts[current_host['hostname']] = current_host

            service = parse_service(children[1:])
            current_host['services'].append(service)
    context = {"hosts": hosts}
    return context


def gm_timestamp(datetime_object):
    return calendar.timegm(datetime_object.utctimetuple())


def get_availability(start_date, end_date):
    url = AVAILABILITY_URL % (gm_timestamp(start_date),
                              gm_timestamp(end_date),
                              settings.NAGIOS_SERVICE_GROUP)
    url = settings.NAGIOS_URL + url
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    return parse_availability(resp.text)


def get_status():
    url = STATUS_URL % settings.NAGIOS_SERVICE_GROUP
    url = settings.NAGIOS_URL + url
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    return parse_status(resp.text)
