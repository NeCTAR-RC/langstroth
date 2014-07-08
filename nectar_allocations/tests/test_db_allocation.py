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
        
    def test_organise_allocations_tree(self):
        allocations_tree = AllocationRequest.organise_allocations_tree()
        self.assertEquals(3, len(allocations_tree))
        
        self.assertEquals('USQ eResearch Services Sandbox', allocations_tree['09']['0999']['099901'][0]['projectName'])
        self.assertEquals('USQ eResearch Services Sandbox', allocations_tree['07']['0701']['070104'][0]['projectName'])
        self.assertEquals('UoM_Trajectory_Inference_Attacks', allocations_tree['08']['0801']['080109'][0]['projectName'])

    def test_restructure_allocations_tree(self):
        name_children_tree = AllocationRequest.restructure_allocations_tree()
        self.assertEquals('allocations', name_children_tree['name'])
        self.assertEquals(3, len(name_children_tree['children']))

        children_2 = name_children_tree['children'][0]
        self.assertEquals('08', children_2['name'])
        self.assertEquals(1, len(children_2['children']))

        children_4 = children_2['children'][0]
        self.assertEquals('0801', children_4['name'])
        self.assertEquals(1, len(children_4['children']))

        children_6 = children_4['children'][0]
        self.assertEquals('080109', children_6['name'])
        self.assertEquals(1, len(children_6['children']))

        project_items = children_6['children'][0]
        self.assertEquals('UoM_Trajectory_Inference_Attacks', project_items['name'])

        children_2 = name_children_tree['children'][1]
        self.assertEquals('09', children_2['name'])
        self.assertEquals(1, len(children_2['children']))

        children_4 = children_2['children'][0]
        self.assertEquals('0999', children_4['name'])
        self.assertEquals(1, len(children_4['children']))

        children_6 = children_4['children'][0]
        self.assertEquals('099901', children_6['name'])
        self.assertEquals(1, len(children_6['children']))

        project_items = children_6['children'][0]
        self.assertEquals('USQ eResearch Services Sandbox', project_items['name'])

        children_2 = name_children_tree['children'][2]
        self.assertEquals('07', children_2['name'])
        self.assertEquals(1, len(children_2['children']))

        children_4 = children_2['children'][0]
        self.assertEquals('0701', children_4['name'])
        self.assertEquals(1, len(children_4['children']))

        children_6 = children_4['children'][0]
        self.assertEquals('070104', children_6['name'])
        self.assertEquals(1, len(children_6['children']))

        project_items = children_6['children'][0]
        self.assertEquals('USQ eResearch Services Sandbox', project_items['name'])
