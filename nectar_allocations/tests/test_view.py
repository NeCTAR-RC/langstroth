from django.test import TestCase


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

    def test_rest_for_project_allocations_from_allocation_request_id(self):
        response = self.client.get(
            "/allocations/rest/applications/1654/history")
        self.assertEqual(200, response.status_code)

    # Site map.

    def test_sitemap(self):
        response = self.client.get(
            "/sitemap.xml")
        self.assertContains(
            response,
            'http://example.com/allocations/applications', 2, 200)
