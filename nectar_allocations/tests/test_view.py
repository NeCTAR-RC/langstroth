from django.test import TestCase

from nectar_allocations.models.forcode import ForCode

class AllocationViewTest(TestCase):
 
    fixtures = ['allocation_requests']
    multi_db = True
    
    def setUp(self):
        ForCode.objects.create(code="1234", name="Biological necessity")
        ForCode.objects.create(code="4321", name="Physical impossibility")
   
    def test_page_index(self):
        response = self.client.get("/allocations/")
        self.assertEqual(200, response.status_code) 
   
    def test_page_visualisation(self):
        response = self.client.get("/allocations/visualisation")
        self.assertEqual(200, response.status_code) 
   
    def test_rest_allocation_tree(self):
        response = self.client.get("/allocations/allocation_tree")
        self.assertEqual(200, response.status_code) 
          
    def test_rest_for_code(self):
        response = self.client.get("/allocations/for_codes")
        self.assertEqual(200, response.status_code)