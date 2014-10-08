from django.test import TestCase

from nectar_allocations.models.allocation import AllocationRequest


class AllocationDBTest(TestCase):

    fixtures = ['allocation_requests']
    multi_db = True

    def setUp(self):
        self.savedShowPrivacy = AllocationRequest.show_private_fields
        return

    def tearDown(self):
        AllocationRequest.show_private_fields = self.savedShowPrivacy
        return

    def test_fixtures(self):
        self.assertEquals(5, AllocationRequest.objects.count())

    def test_allocation_has_project_name(self):
        try:
            allocation0 = AllocationRequest. \
                objects.get(project_name="Shoreview")
        except AllocationRequest.DoesNotExist:
            allocation0 = None
        try:
            allocation1 = AllocationRequest \
                .objects.get(project_name="decadal variability "
                             "in DMS flux in the  Southern Ocean")
        except AllocationRequest.DoesNotExist:
            allocation1 = None
        self.assertIsNotNone(allocation0)
        self.assertEqual(allocation0.instance_quota, 0)
        self.assertIsNotNone(allocation1)
        self.assertEqual(allocation1.instance_quota, 10)

    def test_find_active_allocations(self):
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(2, len(allocations))

    def test_find_active_allocations_including_new_requests(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = '11'
        request0.field_of_research_2 = '22'
        request0.field_of_research_3 = '33'
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(3, len(allocations))

    def test_find_active_allocations_including_third_null_fors(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = '11'
        request0.field_of_research_2 = '22'
        request0.field_of_research_3 = None
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(3, len(allocations))

    def test_find_active_allocations_including_2_null_fors(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = '11'
        request0.field_of_research_2 = None
        request0.field_of_research_3 = None
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(3, len(allocations))

    def test_find_active_allocations_excluding_first_null_fors(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = None
        request0.field_of_research_2 = '22'
        request0.field_of_research_3 = '33'
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(3, len(allocations))

    def test_find_active_allocations_excluding_second_null_fors(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = '11'
        request0.field_of_research_2 = None
        request0.field_of_research_3 = '33'
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(3, len(allocations))

    def test_find_active_allocations_excluding_3_null_fors(self):
        request0 = AllocationRequest(project_name='Project0', status='A')
        request0.field_of_research_1 = None
        request0.field_of_research_2 = None
        request0.field_of_research_3 = None
        request0.save()
        allocations = AllocationRequest.find_active_allocations()
        self.assertEquals(2, len(allocations))

    def test_partition_active_allocations(self):
        sub_allocations = AllocationRequest.partition_active_allocations()
        self.assertEquals(len(sub_allocations), 3)
        sub_allocations.sort(key=lambda summary: summary['project_name']
                             + str(summary['id']))

        sub_allocation = sub_allocations[0]
        self.assertEquals('qqqqqq.edu.au', sub_allocation['institution'])
        self.assertEquals('USQ eResearch Services Sandbox',
                          sub_allocation['project_name'])
        self.assertEquals('099901', sub_allocation['for_6'])
        self.assertEquals('0999', sub_allocation['for_4'])
        self.assertEquals('09', sub_allocation['for_2'])
        self.assertAlmostEqual(1.2, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(2.4, sub_allocation['core_quota'], 2)

        sub_allocation = sub_allocations[1]
        self.assertEquals('qqqqqq.edu.au', sub_allocation['institution'])
        self.assertEquals('USQ eResearch Services Sandbox',
                          sub_allocation['project_name'])
        self.assertEquals('070104', sub_allocation['for_6'])
        self.assertEquals('0701', sub_allocation['for_4'])
        self.assertEquals('07', sub_allocation['for_2'])
        self.assertAlmostEqual(0.8, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(1.6, sub_allocation['core_quota'], 2)

        sub_allocation = sub_allocations[2]
        self.assertEquals('gggg.edu.au', sub_allocation['institution'])
        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          sub_allocation['project_name'])
        self.assertEquals('080109', sub_allocation['for_6'])
        self.assertEquals('0801', sub_allocation['for_4'])
        self.assertEquals('08', sub_allocation['for_2'])
        self.assertAlmostEqual(30.0, sub_allocation['instance_quota'], 2)
        self.assertAlmostEqual(30.0, sub_allocation['core_quota'], 2)

    def test_organise_allocations_tree(self):
        allocations_tree = AllocationRequest.organise_allocations_tree()
        self.assertEquals(3, len(allocations_tree))

        self.assertEquals('USQ eResearch Services Sandbox',
            allocations_tree['09']['0999']['099901'][0]['projectName'])  # noqa
        self.assertEquals('USQ eResearch Services Sandbox',
            allocations_tree['07']['0701']['070104'][0]['projectName'])  # noqa
        self.assertEquals('UoM_Trajectory_Inference_Attacks',
            allocations_tree['08']['0801']['080109'][0]['projectName'])  # noqa

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
        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          project_items['name'])

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
        self.assertEquals('USQ eResearch Services Sandbox',
                          project_items['name'])

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
        self.assertEquals('USQ eResearch Services Sandbox',
                          project_items['name'])

    def test_project_allocations_from_allocation_request_id(self):
        AllocationRequest.show_private_fields = True
        allocation_request_id = 1654
        project_allocations = AllocationRequest \
            .project_allocations_from_allocation_request_id(allocation_request_id)  # noqa

        self.assertEquals(1, len(project_allocations))
        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          project_allocations[0]['project_name'])
        self.assertEquals('2014-01-06', project_allocations[0]['start_date'])
        self.assertEquals('2014-01-31', project_allocations[0]['end_date'])
        expected_usecase = "In this project, an algorithm has been " \
            "developed to infer a persons road trajectory " \
            "using POI information sent to a LBS such as " \
            "Google Maps.\r\n\r\n Please contact [XXXX]."
        self.assertEquals(expected_usecase, project_allocations[0]['use_case'])
        self.assertEquals('Data is stored on a remote server so no storage '
                          'is needed. Please contact [XXXX].',
                          project_allocations[0]['usage_patterns'])

    def test_project_allocations_from_allocation_request_id_with_privacy(self):
        AllocationRequest.show_private_fields = False
        allocation_request_id = 1654
        project_allocations = AllocationRequest \
            .project_allocations_from_allocation_request_id(allocation_request_id)  # noqa

        self.assertEquals(1, len(project_allocations))
        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          project_allocations[0]['project_name'])
        self.assertEquals('2014-01-06', project_allocations[0]['start_date'])
        self.assertEquals('2014-01-31', project_allocations[0]['end_date'])
        self.assertFalse('use_case' in project_allocations[0])
        self.assertFalse('usage_patterns' in project_allocations[0])

    def test_project_allocations_from_allocation_request_id_with_multi_requests(self):  # noqa
        AllocationRequest.show_private_fields = True
        allocation_request_id = 1667
        project_allocations = AllocationRequest \
            .project_allocations_from_allocation_request_id(allocation_request_id)  # noqa
        self.assertEquals(2, len(project_allocations))

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_allocations[0]['project_name'])
        self.assertEquals('2014-02-17', project_allocations[0]['start_date'])
        self.assertEquals('2014-05-17', project_allocations[0]['end_date'])
        expected_usecase = "The cloud instances will be used to set up " \
            "quick demos for researchers at USQ to run test experiments, " \
            "simulations, modelling and calculations.\r\n\r\n " \
            "Please contact [XXXX]."
        self.assertEquals(expected_usecase, project_allocations[0]['use_case'])
        self.assertEquals('Many users and small data sets as well '
                          'as small number of users and large data sets. '
                          'This will vary depending on the tests and the '
                          'resesearch group. Please contact [XXXX].',
                          project_allocations[0]['usage_patterns'])

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_allocations[1]['project_name'])
        self.assertEquals('2014-02-17', project_allocations[1]['start_date'])
        self.assertEquals('2014-05-17', project_allocations[1]['end_date'])
        expected_usecase = "The cloud instances will be used to set up " \
            "quick demos for researchers at USQ to run test experiments, " \
            "simulations, modelling and calculations.\r\n\r\n " \
            "Please contact [XXXX]."
        self.assertEquals(expected_usecase, project_allocations[1]['use_case'])
        self.assertEquals('Many users and small data sets as well '
                          "as small number of users and large data sets. "
                          "This will vary depending on the tests and the "
                          'resesearch group. Please contact [XXXX].',
                          project_allocations[0]['usage_patterns'])

    def test_project_allocations_from_allocation_request_id_with_multi_requests_with_privacy(self):  # noqa
        AllocationRequest.show_private_fields = False
        allocation_request_id = 1667
        project_allocations = AllocationRequest \
            .project_allocations_from_allocation_request_id(allocation_request_id)  # noqa
        self.assertEquals(2, len(project_allocations))

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_allocations[0]['project_name'])
        self.assertEquals('2014-02-17', project_allocations[0]['start_date'])
        self.assertEquals('2014-05-17', project_allocations[0]['end_date'])
        self.assertFalse('use_case' in project_allocations[0])
        self.assertFalse('usage_patterns' in project_allocations[0])

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_allocations[1]['project_name'])
        self.assertEquals('2014-02-17', project_allocations[1]['start_date'])
        self.assertEquals('2014-05-17', project_allocations[1]['end_date'])
        self.assertFalse('use_case' in project_allocations[1])

    def test_projects_from_allocation_request_id(self):
        AllocationRequest.show_private_fields = True
        allocation_request_id = 1654
        project_summary = AllocationRequest \
            .project_from_allocation_request_id(allocation_request_id)

        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          project_summary['project_name'])
        self.assertEquals('2014-01-06', project_summary['start_date'])
        self.assertEquals('2014-01-31', project_summary['end_date'])
        expected_usecase = "In this project, an algorithm has been " \
            "developed to infer a persons road trajectory using POI " \
            "information sent to a LBS such as Google Maps." \
            "\r\n\r\n Please contact [XXXX]."
        self.assertEquals(expected_usecase, project_summary['use_case'])
        self.assertEquals('Data is stored on a remote server so no '
                          'storage is needed. Please contact [XXXX].',
                          project_summary['usage_patterns'])
        self.assertEquals(30, project_summary['instance_quota'])
        self.assertEquals(30, project_summary['core_quota'])
        self.assertEquals('2014-01-05', project_summary['submit_date'])
        self.assertEquals('2014-02-16 23:21:59',
                          project_summary['modified_time'])
        self.assertEquals(2, project_summary['cores'])
        self.assertEquals(30, project_summary['instances'])
        self.assertEquals('080109', project_summary['field_of_research_1'])
        self.assertEquals(100, project_summary['for_percentage_1'])
        self.assertEquals(None, project_summary['field_of_research_2'])
        self.assertEquals(0, project_summary['for_percentage_2'])
        self.assertEquals(None, project_summary['field_of_research_3'])
        self.assertEquals(0, project_summary['for_percentage_3'])

    def test_projects_from_allocation_request_id_with_privacy(self):
        AllocationRequest.show_private_fields = False
        allocation_request_id = 1654
        project_summary = AllocationRequest \
            .project_from_allocation_request_id(allocation_request_id)

        self.assertEquals('UoM_Trajectory_Inference_Attacks',
                          project_summary['project_name'])
        self.assertEquals('2014-01-06', project_summary['start_date'])
        self.assertEquals('2014-01-31', project_summary['end_date'])
        self.assertFalse('use_case' in project_summary)
        self.assertFalse('usage_patterns' in project_summary)
        self.assertEquals(30, project_summary['instance_quota'])
        self.assertEquals(30, project_summary['core_quota'])
        self.assertEquals('2014-01-05', project_summary['submit_date'])
        self.assertEquals('2014-02-16 23:21:59',
                          project_summary['modified_time'])
        self.assertEquals(2, project_summary['cores'])
        self.assertEquals(30, project_summary['instances'])
        self.assertEquals('080109', project_summary['field_of_research_1'])
        self.assertEquals(100, project_summary['for_percentage_1'])
        self.assertEquals(None, project_summary['field_of_research_2'])
        self.assertEquals(0, project_summary['for_percentage_2'])
        self.assertEquals(None, project_summary['field_of_research_3'])
        self.assertEquals(0, project_summary['for_percentage_3'])

    def test_projects_from_allocation_request_id_with_multi_requests(self):
        AllocationRequest.show_private_fields = True
        allocation_request_id = 1667
        project_summary = AllocationRequest \
            .project_from_allocation_request_id(allocation_request_id)

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_summary['project_name'])
        self.assertEquals('2014-02-17', project_summary['start_date'])
        self.assertEquals('2014-05-17', project_summary['end_date'])
        expected_usecase = "The cloud instances will be used to set up quick " \
            "demos for researchers at USQ to run test experiments, " \
            "simulations, modelling and calculations.\r\n\r\n " \
            "Please contact [XXXX]."
        self.assertEquals(expected_usecase, project_summary['use_case'])
        self.assertEquals('Many users and small data sets as well '
                          'as small number of users and large data sets. '
                          'This will vary depending on the tests and the '
                          'resesearch group. Please contact [XXXX].',
                          project_summary['usage_patterns'])
        self.assertEquals(2, project_summary['instance_quota'])
        self.assertEquals(4, project_summary['core_quota'])
        self.assertEquals('2014-02-17', project_summary['submit_date'])
        self.assertEquals('2014-03-24 22:01:54',
                          project_summary['modified_time'])
        self.assertEquals(5, project_summary['cores'])
        self.assertEquals(3, project_summary['instances'])
        self.assertEquals('099901', project_summary['field_of_research_1'])
        self.assertEquals(60, project_summary['for_percentage_1'])
        self.assertEquals('070104', project_summary['field_of_research_2'])
        self.assertEquals(40, project_summary['for_percentage_2'])
        self.assertEquals(None, project_summary['field_of_research_3'])
        self.assertEquals(0, project_summary['for_percentage_3'])

    def test_projects_from_allocation_request_id_with_multi_requests_with_privacy(self):  # noqa
        AllocationRequest.show_private_fields = False
        allocation_request_id = 1667
        project_summary = AllocationRequest \
            .project_from_allocation_request_id(allocation_request_id)

        self.assertEquals('USQ eResearch Services Sandbox',
                          project_summary['project_name'])
        self.assertEquals('2014-02-17', project_summary['start_date'])
        self.assertEquals('2014-05-17', project_summary['end_date'])
        self.assertFalse('use_case' in project_summary)
        self.assertFalse('usage_patterns' in project_summary)
        self.assertEquals(2, project_summary['instance_quota'])
        self.assertEquals(4, project_summary['core_quota'])
        self.assertEquals('2014-02-17', project_summary['submit_date'])
        self.assertEquals('2014-03-24 22:01:54',
                          project_summary['modified_time'])
        self.assertEquals(5, project_summary['cores'])
        self.assertEquals(3, project_summary['instances'])
        self.assertEquals('099901', project_summary['field_of_research_1'])
        self.assertEquals(60, project_summary['for_percentage_1'])
        self.assertEquals('070104', project_summary['field_of_research_2'])
        self.assertEquals(40, project_summary['for_percentage_2'])
        self.assertEquals(None, project_summary['field_of_research_3'])
        self.assertEquals(0, project_summary['for_percentage_3'])
