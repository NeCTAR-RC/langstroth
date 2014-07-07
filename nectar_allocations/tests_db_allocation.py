from django.test import TestCase

from nectar_allocations.models import AllocationRequest

class AllocationDBTest(TestCase):

    fixtures = ['allocation_requests']
    multi_db = True

    def setUp(self):
        return
        
    def test_fixtures(self):
        self.assertEquals(AllocationRequest.objects.count(), 2)

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
        

