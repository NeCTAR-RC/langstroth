from django.utils import unittest
import json
from utilities.diff import Diff
from os import path

from nectar_allocations.models.allocation import AllocationRequest

def path_for_tests(file_name):
    """Returns the absolute path to the merged dirname of the pathname and
    filename."""
    return path.abspath(path.join(path.dirname(__file__), file_name))


@classmethod
def organise_allocations_tree(cls):

    child0 = {
        'id': 199L,
        'projectName': u'CharacterisationVL - [Additional resource]',
        'institution': u'monash.edu',
        'coreQuota': 80.0,
        'instanceQuota': 80.0,
    }

    child1 = {
        'id': 420L,
        'projectName': u'UTas Climate Change and Health Adaptions',
        'institution': u'utas.edu.au',
        'coreQuota': 3.2,
        'instanceQuota': 3.2,
    }

    child2 = {
        'id': 253L,
        'projectName': u'Sport and Recreation Spatial',
        'institution': u'ballarat.edu.au',
        'coreQuota': 1.2,
        'instanceQuota': 1.2,
    }

    allocations_tree = {
        u'11': {
            u'11': {
                u'11': [
                    child0,
                    child1,
                ]
            },
            u'1106': {
                u'110699': [
                    child2,
                ]
            }
        }
    }
    return allocations_tree


class AllocationTest(unittest.TestCase):

    request0 = None
    request1 = None

    old_organise_allocations_tree = None

    def setUp(self):
        self.request0 = AllocationRequest(project_name="Project X", status="E")
        self.request1 = AllocationRequest(project_name="Project Y", status="X")
        self.old_organise_allocations_tree = \
            AllocationRequest.organise_allocations_tree
        AllocationRequest.organise_allocations_tree = organise_allocations_tree

    def tearDown(self):
        self.request0 = None
        self.request1 = None
        AllocationRequest.organise_allocations_tree = \
            self.old_organise_allocations_tree

    def test_request_has_project_name(self):

        self.assertEqual(self.request0.project_name, 'Project X')
        self.assertEqual(self.request1.project_name, 'Project Y')

    def test_request_has_status(self):
        self.assertEqual(self.request0.status, 'E')
        self.assertEqual(self.request1.status, 'X')

    def test_strip_email_group_prefix_unknown(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'unkown.murdoch.edu.au'),
            'unkown.murdoch.edu.au')

    def test_strip_email_group_prefix_student(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'student.murdoch.edu.au'),
            'murdoch.edu.au')

    def test_strip_email_group_prefix_studentmail(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'studentmail.newcastle.edu.au'),
            'newcastle.edu.au')

    def test_strip_email_group_prefix_my(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'my.jcu.edu.au'),
            'jcu.edu.au')

    def test_strip_email_group_prefix_ems(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'ems.rmit.edu.au'),
            'rmit.edu.au')

    def test_strip_email_group_prefix_exchange(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'exchange.swin.edu.au'),
            'swin.edu.au')

    def test_strip_email_group_prefix_groupwise(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'groupwise.swin.edu.au'),
            'swin.edu.au')

    def test_strip_email_group_noprefix(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'uon.edu.au'),
            'uon.edu.au')

    def test_strip_email_group_translates_domain_griffith(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'griffithuni.edu.au'),
            'griffith.edu.au')

    def test_strip_email_group_translates_domain_uwa(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'waimr.uwa.edu.au'),
            'uwa.edu.au')

    def test_strip_email_group_translates_domain_unisydney(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'uni.sydney.edu.au'),
            'sydney.edu.au')

    def test_strip_email_group_translates_domain_usydney(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'usyd.edu.au'),
            'sydney.edu.au')

    def test_strip_email_group_translates_domain_myune(self):
        self.assertEqual(AllocationRequest.strip_email_sub_domains(
            'myune.edu.au'),
            'une.edu.au')

    def test_strip_email_group_translates_selection(self):
        file_name = path_for_tests("institution_cleaning.json")
        with open(file_name) as institutions_file:
            institutions = json.load(institutions_file)
        for institution in institutions:
            self.assertEqual(AllocationRequest.strip_email_sub_domains(
                institution['original']),
                institution['processed'])

    def test_extract_email_domain(self):
        self.assertEqual(AllocationRequest.extract_email_domain(
            'ferd@myune.edu.au'),
            'myune.edu.au')

    def test_is_valid_for_null(self):
        self.assertFalse(AllocationRequest.is_valid_for_code(None))

    def test_is_valid_for_none_null(self):
        self.assertTrue(AllocationRequest.is_valid_for_code('00'))

    def test_apply_for_code_to_summary_for6(self):
        allocation_summary = dict()
        code = '123456'
        AllocationRequest.apply_for_code_to_summary(allocation_summary, code)
        self.assertEqual(allocation_summary['for_6'], '123456')
        self.assertEqual(allocation_summary['for_4'], '1234')
        self.assertEqual(allocation_summary['for_2'], '12')

    def test_apply_for_code_to_summary_for4(self):
        allocation_summary = dict()
        code = '1234'
        AllocationRequest.apply_for_code_to_summary(allocation_summary, code)
        self.assertEqual(allocation_summary['for_6'], '1234')
        self.assertEqual(allocation_summary['for_4'], '1234')
        self.assertEqual(allocation_summary['for_2'], '12')

    def test_apply_for_code_to_summary_for2(self):
        allocation_summary = dict()
        code = '12'
        AllocationRequest.apply_for_code_to_summary(allocation_summary, code)
        self.assertEqual(allocation_summary['for_6'], '12')
        self.assertEqual(allocation_summary['for_4'], '12')
        self.assertEqual(allocation_summary['for_2'], '12')

    def test_redact_no_emails(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact someone for more information'),
            'Please contact someone for more information')

    def test_redact_one_email(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au for more information'),
            'Please contact [XXXX] for more information')

    def test_redact_one_email_with_period(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au.'),
            'Please contact [XXXX].')

    def test_redact_one_email_with_comma(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au,'),
            'Please contact [XXXX],')

    def test_redact_one_email_with_question(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au?'),
            'Please contact [XXXX]?')

    def test_redact_one_email_with_exclamation(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au!'),
            'Please contact [XXXX]!')

    def test_redact_one_email_with_bracket(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au)'),
            'Please contact [XXXX])')

    def test_redact_two_emails_in_field(self):
        self.assertEqual(AllocationRequest.redact_all_emails(
            'Please contact joe.bloggs@unimelb.edu.au '
            'or fred_nerk@google.com for more information'),
            'Please contact [XXXX] '
            'or [XXXX] for more information')

#     def test_organise_allocations_tree(self):
#         allocations = [
#            {'id': 934L,
#             'for_2': u'19',
#             'for_4': u'1902',
#             'for_6': u'190201',
#             'core_quota': 0.5,
#             'instance_quota': 1.0,
#             'institution': u'deakin.edu.au',
#             'project_name': u'Deakin_Bonza',
#             }]

    def test_restructure_allocations_tree(self):

        child0 = {
            'id': 199L,
            'name': u'CharacterisationVL - [Additional resource]',
            'institution': u'monash.edu',
            'coreQuota': 80.0,
            'instanceQuota': 80.0,
        }

        child1 = {
            'id': 420L,
            'name': u'UTas Climate Change and Health Adaptions',
            'institution': u'utas.edu.au',
            'coreQuota': 3.2,
            'instanceQuota': 3.2,
        }

        child2 = {
            'id': 253L,
            'name': u'Sport and Recreation Spatial',
            'institution': u'ballarat.edu.au',
            'coreQuota': 1.2,
            'instanceQuota': 1.2,
        }

        expected_allocations_tree = {
            'name': 'allocations',
            'children': [
                {
                    'name': u'11',
                    'children': [
                        {
                            'name': u'11',
                            'children': [{
                                'name': u'11',
                                'children': [
                                    child0,
                                    child1,
                                ]
                            }]
                        },
                        {
                            'name': u'1106',
                            'children': [{
                                'name': u'110699',
                                'children': [
                                    child2
                                ]
                            }]
                        }
                    ]
                }
            ]
        }

        actual_allocations_tree = AllocationRequest \
            .restructure_allocations_tree()

        self.assertTrue('name' in actual_allocations_tree)
        self.assertTrue('children' in actual_allocations_tree)
        self.assertEqual('allocations', actual_allocations_tree['name'])
        expected = self.sort_tree(expected_allocations_tree['children'])
        actual = self.sort_tree(actual_allocations_tree['children'])
        df = Diff(expected, actual)
        self.assertEqual([], df.difference)

    def sort_tree(self, allocations):
        """Sort allocations tree.

         Needed since the JSON diff code is sensitive to key order.
        """
        # allocation_tree at the top level is a list.
        allocations.sort(key=lambda allocation: allocation['name'])
        for allocation in allocations:
            if 'children' in allocation:
                allocations = allocation['children']
                self.sort_tree(allocations)
