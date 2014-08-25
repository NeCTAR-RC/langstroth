from django.test import TestCase

import json
from os import path

from nectar_allocations.models.allocation import AllocationRequest
from utilities.diff import Diff

class JsonIntegrationTest(TestCase):
 
    fixtures = ['nectar_allocations_dump_all']
    multi_db = True

    def setUp(self):
        # reference_file_path = '/langstroth/data/allocation_tree.json'
        reference_file_path = path.join(path.dirname(__file__), "../../langstroth/data/allocation_tree.json")
        with open(reference_file_path) as allocations_tree_file:    
            self.expected_allocations_tree = json.load(allocations_tree_file)
        found_allocations_tree = AllocationRequest.restructure_allocations_tree()
        self.actual_allocations_tree = found_allocations_tree['children']
        
    def test_fixtures(self):
        self.assertEquals(796, AllocationRequest.objects.count())
        
    def test_tree_top_level(self):
        self.assertEquals(21, len(self.actual_allocations_tree))
        self.assertEquals(21, len(self.expected_allocations_tree))
   
    def test_json_generator_allocation_tree(self):
        expected = self.sort_tree(self.expected_allocations_tree)
        actual = self.sort_tree(self.actual_allocations_tree)
        df = Diff(expected, actual)
        self.assertEqual([], df.difference)
     
    # Need to sort allocations tree since the JSON diff code 
    # is sensitive to key order.  
    def sort_tree(self, allocations):
        # allocation_tree at the top level is a list.
        allocations.sort(key=lambda allocation: allocation['name'])
        for allocation in allocations:
            if 'children' in allocation:
                allocations = allocation['children']
                self.sort_tree(allocations)
