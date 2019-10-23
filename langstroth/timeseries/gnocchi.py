
import datetime
from dateutil import parser
import re
import time

from gnocchiclient import client

from langstroth import keystone


GNOCCHI_API_VERSION = '1'


resource_type_map = {
    'az': 'availability-zone',
}


class GnocchiTimeSeries(object):

    def __init__(self):
        super(GnocchiTimeSeries, self).__init__()
        self.client = self._get_client()

    @staticmethod
    def _get_client():
        auth = keystone.get_auth_session()
        return client.Client(GNOCCHI_API_VERSION, auth)

    def get_data(self, targets, granularity, date_from):

        data = []
        granularity = 86400
        today = datetime.datetime.now()
        if date_from == '-6months':
            start = today - datetime.timedelta(days=365 / 2)
        elif date_from == '-1months':
            start = today - datetime.timedelta(days=30)
            granularity = 3600
        elif date_from == '-1years':
            start = today - datetime.timedelta(days=365)
        elif date_from == '-3years':
            start = today - datetime.timedelta(days=3 * 365)
        else:
            start = today - datetime.timedelta(days=365 / 2)

        date_from = datetime.datetime(2015, 9, 29)
        for target in targets:
            alias = target[0]
            series = target[1]
            if 'sumSeries' in series:
                items = re.search(
                    r'sumSeries\((?P<series_list>.*)\)', series).groupdict()
                series = items.get('series_list').split(',')
                metric_list = []
                for series in series:
                    resource_type, resource_name, metric = series.split('.')
                    resource_type = resource_type_map[resource_type]
                    resource = self.client.resource.search(
                        resource_type=resource_type,
                        query={'=': {'id': resource_name}})[0]

                    gmetric = self.client.metric.get(
                        resource_id=resource.get('id'), metric=metric)
                    metric_list.append(gmetric.get('id'))
                measures = self.client.metric.aggregation(
                    metrics=metric_list,
                    granularity=granularity,
                    reaggregation='sum',
                    start=start)
            else:

                resource_type, resource_name, metric = series.split('.')
                resource_type = resource_type_map[resource_type]

                try:
                    resource = self.client.resource.search(
                        resource_type=resource_type,
                        query={'=': {'id': resource_name}})[0]
                except Exception:
                    continue
                try:
                    measures = self.client.metric.get_measures(
                        resource_id=resource.get('id'),
                        metric=metric,
                        granularity=granularity,
                        start=start)
                except Exception:
                    measures = []

            formatted_data = []
            for measure in measures:
                formatted_data.append(
                    [measure[2],
                     time.mktime(parser.parse(measure[0]).timetuple())])
            data.append({'target': alias, 'datapoints': formatted_data})

        return data
