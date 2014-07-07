from django.utils import unittest
import json
from os import path

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
    
    def test_request_has_project_name(self):
           
        self.assertEqual(self.request0.project_name, 'Project X')
        self.assertEqual(self.request1.project_name, 'Project Y')

    def test_request_has_status(self):            
        self.assertEqual(self.request0.status, 'E')
        self.assertEqual(self.request1.status, 'X')
        
    def test_strip_email_group_prefix_student(self):
        self.assertEqual(AllocationRequest.strip_email_group('student.murdoch.edu.au'), 'murdoch.edu.au')
        
    def test_strip_email_group_prefix_studentmail(self):
        self.assertEqual(AllocationRequest.strip_email_group('studentmail.newcastle.edu.au'), 'newcastle.edu.au')
        
    def test_strip_email_group_prefix_my(self):
        self.assertEqual(AllocationRequest.strip_email_group('my.jcu.edu.au'), 'jcu.edu.au')
        
    def test_strip_email_group_prefix_ems(self):
        self.assertEqual(AllocationRequest.strip_email_group('ems.rmit.edu.au'), 'rmit.edu.au')
        
    def test_strip_email_group_prefix_exchange(self):
        self.assertEqual(AllocationRequest.strip_email_group('exchange.swin.edu.au'), 'swin.edu.au')
        
    def test_strip_email_group_prefix_groupwise(self):
        self.assertEqual(AllocationRequest.strip_email_group('groupwise.swin.edu.au'), 'swin.edu.au')
        
    def test_strip_email_group_noprefix(self):
        self.assertEqual(AllocationRequest.strip_email_group('uon.edu.au'), 'uon.edu.au')
        
    def test_strip_email_group_translates_domain_griffith(self):
        self.assertEqual(AllocationRequest.strip_email_group('griffithuni.edu.au'), 'griffith.edu.au')
        
    def test_strip_email_group_translates_domain_uwa(self):
        self.assertEqual(AllocationRequest.strip_email_group('waimr.uwa.edu.au'), 'uwa.edu.au')
        
    def test_strip_email_group_translates_domain_unisydney(self):
        self.assertEqual(AllocationRequest.strip_email_group('uni.sydney.edu.au'), 'sydney.edu.au')
        
    def test_strip_email_group_translates_domain_usydney(self):
        self.assertEqual(AllocationRequest.strip_email_group('usyd.edu.au'), 'sydney.edu.au')
        
    def test_strip_email_group_translates_domain_myune(self):
        self.assertEqual(AllocationRequest.strip_email_group('myune.edu.au'), 'une.edu.au')
        
    def test_strip_email_group_translates_selection(self):
        file_name = path.join(path.dirname(__file__), "institution_cleaning.json")
        with open(file_name) as institutions_file:    
            institutions = json.load(institutions_file)
        for institution in institutions:       
            self.assertEqual(AllocationRequest.strip_email_group(institution['original']), institution['processed'])       
        
    def test_extract_email_domain(self):
        self.assertEqual(AllocationRequest.extract_email_domain('ferd@myune.edu.au'), 'myune.edu.au')
        
#     def test_extract_institution(self):
        
        
        
