from django.test import TestCase


class AllocationViewTest(TestCase):

    def test_page_index(self):
        response = self.client.get("/allocations/")
        self.assertEqual(200, response.status_code)

    def test_page_project(self):
        response = self.client.get(
            "/allocations/applications/1654/approved")
        self.assertEqual(200, response.status_code)
