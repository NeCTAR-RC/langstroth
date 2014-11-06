from django.test import TestCase

import httpretty
import json


usage_statistics = [
    {
        "target": "core_count",
        "datapoints": [
            [20.0, 1324216800],
        ]
    },
    {
        "target": "instance_count",
        "datapoints": [
            [10.0, 1324303200],
        ]
    }
]


class AllocationViewTest(TestCase):

    fixtures = ['allocation_requests']
    multi_db = True

    # Web pages

    def test_page_index(self):
        response = self.client.get("/allocations/")
        self.assertEqual(200, response.status_code)

    def test_page_visualisation(self):
        response = self.client.get(
            "/allocations/applications/approved/visualisation")
        self.assertEqual(200, response.status_code)

    def test_page_project(self):
        response = self.client.get(
            "/allocations/applications/1654/approved")
        self.assertEqual(200, response.status_code)

    def test_page_project_allocations(self):
        response = self.client.get(
            "/allocations/applications/1654/approved")
        self.assertEqual(200, response.status_code)

    # Web services with JSON pay loads.

    def test_rest_allocation_tree(self):
        response = self.client.get(
            "/allocations/rest/applications/approved/tree")
        self.assertEqual(200, response.status_code)

    def test_rest_for_code(self):
        response = self.client.get("/allocations/rest/for_codes")
        self.assertEqual(200, response.status_code)

    def test_rest_for_project_from_allocation_request_id(self):
        response = self.client.get(
            "/allocations/rest/applications/1654/approved")
        self.assertEqual(200, response.status_code)

    @httpretty.activate
    def test_rest_project_summary_response(self):
        httpretty.register_uri(
            httpretty.GET,
            'http://graphite.dev.rc.nectar.org.au/render/',
            body=json.dumps(usage_statistics),
            content_type="application/json")

        response = self.client.get(
            "/allocations/rest/applications/1654/approved")
        self.assertEqual(200, response.status_code)
        result = json.loads(response.content)
        assert result['used_cores'] == 20
        assert result['used_instances'] == 10

    def test_rest_for_project_allocations_from_allocation_request_id(self):
        response = self.client.get(
            "/allocations/rest/applications/1654/history")
        self.assertEqual(200, response.status_code)
