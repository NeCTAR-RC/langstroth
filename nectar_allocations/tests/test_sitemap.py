from django.test import TestCase
import mock
from datetime import datetime

from nectar_allocations.models.allocation import AllocationRequest
from nectar_allocations.sitemap import AllocationsSitemap


class SitemapTest(TestCase):

    @mock.patch(
        'nectar_allocations.models.allocation.AllocationRequest.'
        'find_active_allocations')
    def test_items(self, mock_find_active_allocations):
        request0 = AllocationRequest(project_description="Project X",
                                     status="E")
        request1 = AllocationRequest(project_description="Project Y",
                                     status="X")
        expected_items = [request0, request1]

        mock_find_active_allocations.return_value = expected_items
        site_map = AllocationsSitemap()
        actual_items = site_map.items()
        self.assertListEqual(expected_items, actual_items)

    def test_lastmod(self):
        expected_datetime = datetime(2014, 10, 13)
        request0 = AllocationRequest(project_description="Project X",
                                     status="E")
        request0.modified_time = expected_datetime
        site_map = AllocationsSitemap()
        actual_modification_datetime = site_map.lastmod(request0)
        self.assertEquals(expected_datetime, actual_modification_datetime)

    def test_location(self):
        request0 = AllocationRequest(project_description="Project X",
                                     status="E")
        request0.id = 12345
        site_map = AllocationsSitemap()
        actual_location = site_map.location(request0)
        expected_location = '/allocations/applications/12345/approved'
        self.assertEquals(expected_location, actual_location)
