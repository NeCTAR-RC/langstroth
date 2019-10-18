import logging
import calendar

import requests
import cssselect
import lxml.etree
from django.conf import settings


LOG = logging.getLogger(__name__)

SERVICE_NAMES = {'http_cinder-api': 'Volume',
                 'http_aodh-api': 'Alarming',
                 'https': 'Webserver',
                 'http_dashboard': 'Dashboard',
                 'http_accounts': 'Accounts',
                 'http_ceilometer-api': 'Ceilometer',
                 'http_murano-api': 'Application Catalog',
                 'http_glance-registry': 'Image Registry',
                 'http_keystone-adm': 'Identity Admin',
                 'http_keystone-pub': 'Identity',
                 'http_neutron-api': 'Network',
                 'http_swift-api': 'Object Store',
                 'http_ec2': 'EC2',
                 'http_nova-api': 'Compute',
                 'http_nova-api-metadata': 'Instance Metadata',
                 'http_heat-api': 'Orchestration',
                 'http_gnocchi-api': 'Metric',
                 'http_glance-api': 'Image',
                 'http_designate-api': 'DNS',
                 'http_manila-api': 'Shared Filesystem',
                 'http_sahara-api': 'Data Processing',
                 'http_trove-api': 'Database',
                 'tempest_auckland_compute': 'auckland',
                 'tempest_intersect-01_compute': 'intersect-01',
                 'tempest_intersect-02_compute': 'intersect-02',
                 'tempest_melbourne-np_compute': 'melbourne-np',
                 'tempest_melbourne-qh2_compute': 'melbourne-qh2',
                 'tempest_monash-01_compute': 'monash-01',
                 'tempest_monash-02_compute': 'monash-02',
                 'tempest_nci_compute': 'NCI',
                 'tempest_pawsey_compute': 'pawsey-01',
                 'tempest_qld_compute': 'QRIScloud',
                 'tempest_sa_compute': 'sa',
                 'tempest_swinburne-01_compute': 'swinburne',
                 'tempest_tasmania_compute': 'tasmania',
                 'tempest_coreservices_compute': 'Core Services',
                 'tempest_melbourne_compute': 'QH2-Test',
                 'tempest_lani_compute': 'Lani',
                 'tempest_luna_compute': 'Luna',
}


def parse_service_availability(service):
    host, service, ok, warn, unknown, crit, undet = service.getchildren()
    nagios_service_name = "".join([t for t in service.itertext()])
    return {"name": nagios_service_name,
            "ok": ok.text.split(' ')[0],
            "warning": warn.text.split(' ')[0],
            "unknown": unknown.text.split(' ')[0],
            "critical": crit.text.split(' ')[0]}


def parse_availability(html, service_group):
    tr = cssselect.GenericTranslator()
    h = lxml.etree.HTML(html)
    table = None
    for i, e in enumerate(h.xpath(tr.css_to_xpath('.dataTitle')), -1):
        if service_group not in e.text:
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
    service_name = SERVICE_NAMES.get(name)
    if not service_name:
        raise ValueError
    return {
        'name': name,
        'display_name': service_name,
        'status': service_columns[1].text,
        'last_checked': service_columns[2].text,
        'duration': service_columns[3].text}


def parse_status(html, service_group):
    tr = cssselect.GenericTranslator()
    h = lxml.etree.HTML(html)
    table = None
    for i, e in enumerate(h.xpath(tr.css_to_xpath('.statusTitle')), -1):
        if service_group not in e.text:
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

            try:
                service = parse_service(children[1:])
            except ValueError:
                pass
            else:
                current_host['services'].append(service)
    context = {"hosts": hosts}
    return context


def gm_timestamp(datetime_object):
    return calendar.timegm(datetime_object.utctimetuple())


def get_availability(start_date, end_date,
                     service_group=settings.NAGIOS_SERVICE_GROUP):
    query = settings.AVAILABILITY_QUERY_TEMPLATE % (
        gm_timestamp(start_date),
        gm_timestamp(end_date),
        service_group)
    url = settings.NAGIOS_URL + query
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    return parse_availability(resp.text, service_group)


def get_status(service_group=settings.NAGIOS_SERVICE_GROUP):
    query = settings.STATUS_QUERY_TEMPLATE % service_group
    url = settings.NAGIOS_URL + query
    resp = requests.get(url, auth=settings.NAGIOS_AUTH)
    return parse_status(resp.text, service_group)
