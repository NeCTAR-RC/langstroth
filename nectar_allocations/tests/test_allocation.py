from django.utils import unittest

from nectar_allocations.models.allocation import AllocationRequest

class AllocationTest(unittest.TestCase):
    
    request0 = None
    request1 = None
    
    def setUp(self):
        self.request0 = AllocationRequest(project_name="Project X", status="E")
        self.request1 = AllocationRequest(project_name="Project Y", status="X")

    def tearDown(self):
        self.request0 = None
        self.request1 = None
    
    def test_request_has_code(self):
           
        self.assertEqual(self.request0.project_name, 'Project X')
        self.assertEqual(self.request1.project_name, 'Project Y')

    def test_request_has_name(self):            
        self.assertEqual(self.request0.status, 'E')
        self.assertEqual(self.request1.status, 'X')
