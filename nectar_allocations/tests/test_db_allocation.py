from django.test import TestCase

from nectar_allocations.models.allocation import AllocationRequest

class AllocationDBTest(TestCase):

    fixtures = ['allocation_requests']
    multi_db = True

    def setUp(self):
        return
        
    def test_fixtures(self):
        self.assertEquals(AllocationRequest.objects.count(), 4)

    def test_allocation_has_project_name(self):
        try:
            allocation0 = AllocationRequest.objects.get(project_name="Shoreview")
        except AllocationRequest.DoesNotExist:
            allocation0 = None
        try:
            allocation1 = AllocationRequest.objects.get(project_name="decadal variability in DMS flux in the  Southern Ocean")
        except AllocationRequest.DoesNotExist:
            allocation1 = None
        self.assertIsNotNone(allocation0)
        self.assertEqual(allocation0.instance_quota, 0)
        self.assertIsNotNone(allocation1)
        self.assertEqual(allocation1.instance_quota, 10)
        
    def test_find_active_allocations(self):
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(len(allocations), 2)
        
    def test_partition_active_allocations(self):
        sub_allocations = AllocationRequest.partition_active_allocations()
        self.assertEquals(len(sub_allocations), 3)
        sub_allocations.sort(key=lambda summary: summary['project_name'])
        
        sub_allocation = sub_allocations[0]
        self.assertEquals('usq.edu.au', sub_allocation['institution'])
        self.assertEquals('USQ eResearch Services Sandbox', sub_allocation['project_name'])
        self.assertEquals('099901', sub_allocation['for_6'])
        self.assertEquals('0999', sub_allocation['for_4'])
        self.assertEquals('09', sub_allocation['for_2'])
        self.assertAlmostEqual(1.2, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(2.4, sub_allocation['core_quota'], 2)
        
        sub_allocation = sub_allocations[1]
        self.assertEquals('usq.edu.au', sub_allocation['institution'])
        self.assertEquals('USQ eResearch Services Sandbox', sub_allocation['project_name'])
        self.assertEquals('070104', sub_allocation['for_6'])
        self.assertEquals('0701', sub_allocation['for_4'])
        self.assertEquals('07', sub_allocation['for_2'])
        self.assertAlmostEqual(0.8, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(1.6, sub_allocation['core_quota'], 2)
        
        sub_allocation = sub_allocations[2]
        self.assertEquals('unimelb.edu.au', sub_allocation['institution'])
        self.assertEquals('UoM_Trajectory_Inference_Attacks', sub_allocation['project_name'])
        self.assertEquals('080109', sub_allocation['for_6'])
        self.assertEquals('0801', sub_allocation['for_4'])
        self.assertEquals('08', sub_allocation['for_2'])
        self.assertAlmostEqual(30.0, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(30.0, sub_allocation['core_quota'], 2)
