from django.test import TestCase
import mock
from datetime import date
from langstroth import graphite
from nectar_allocations.services import project_details


class TestProjectDetails(TestCase):

    @mock.patch('requests.Response')
    @mock.patch('langstroth.graphite.get')
    @mock.patch('nectar_allocations.services.project_details.date')
    def test_project_details_queries_graphite(
            self, mock_date, mock_get, mock_response):
        mock_date.today.return_value = date(2014, 12, 1)
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        response = project_details.find_current_project_resource_usage('xxxxx')
        targetStr0 = "alias(smartSummarize(tenant.xxxxx.total_instances, " + \
            "\"1d\", \"max\"), \"instance_count\")"
        target0 = graphite.Target(targetStr0)
        targetStr1 = "alias(smartSummarize(tenant.xxxxx.used_vcpus, " + \
            "\"1d\", \"max\"), \"core_count\")"
        target1 = graphite.Target(targetStr1)
        mock_get.assert_called_with(
            from_date='20141201', targets=[target0, target1])
        assert response == []

    @mock.patch('requests.Response')
    @mock.patch('langstroth.graphite.get')
    @mock.patch('langstroth.graphite.filter_null_datapoints')
    def test_project_details_are_null_filtered(
            self, mock_filter_null_datapoints, mock_get, mock_response):
        mock_response.json.return_value = {'yyy'}
        mock_get.return_value = mock_response
        mock_filter_null_datapoints.return_value = []
        response = project_details.find_current_project_resource_usage("yyy")
        mock_filter_null_datapoints.assert_called_with({'yyy'})
        assert response == []
