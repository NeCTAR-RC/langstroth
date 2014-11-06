from django.test import TestCase
import mock
from datetime import date
from langstroth import graphite
from nectar_allocations.services import project_details

'''
For mocking dates see: http://www.williamjohnbert.com/2011/07/
     how-to-unit-testing-in-django-with-mocking-and-patching/
'''


class ListMatcher:

    '''
    Check that a list is equal to another list in
    both length and elements.

    Depends on the list elements having equals methods.
    '''

    def __init__(self, alist):
        self.list = alist

    def __eq__(self, other_list):
        if len(self.list) != len(other_list):
            return False
        for item, other_item in zip(self.list, other_list):
            if item != other_item:
                return False
        return True


class WrappedDate(date):

    '''
    Wrap date with fake date since date can't be mocked directly.
    '''
    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)


class TestProjectDetails(TestCase):

    @mock.patch('requests.Response')
    @mock.patch('langstroth.graphite.get')
    @mock.patch('nectar_allocations.services.project_details.date', WrappedDate)
    def test_project_details_queries_graphite(self, mock_get, mock_response):
        from datetime import date   # NOQA
        WrappedDate.today = classmethod(lambda cls: date(2014, 12, 1))
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        response = project_details.find_current_project_resource_usage('xxxxx')
        targetStr0 = "alias(smartSummarize(tenant.xxxxx.total_instances, " + \
            "\"1d\", \"max\"), \"instance_count\")"
        target0 = graphite.Target(targetStr0)
        targetStr1 = "alias(smartSummarize(tenant.xxxxx.used_vcpus, " + \
            "\"1d\", \"max\"), \"core_count\")"
        target1 = graphite.Target(targetStr1)
        mock_get.assert_called_with(from_date='20141201',
                                    targets=ListMatcher([target0, target1]))
        assert response == []

    @mock.patch('requests.Response.json')
    @mock.patch('langstroth.graphite.filter_null_datapoints')
    def test_project_details_are_null_filtered(
            self, mock_filter_null_datapoints, mock_json):
        mock_json.return_value = {'yyy'}
        mock_filter_null_datapoints.return_value = []
        response = project_details.find_current_project_resource_usage("yyy")
        mock_filter_null_datapoints.assert_called_with({'yyy'})
        assert response == []
