from django.db import models
from django.conf import settings
from django.db.models import Q
import re
from operator import itemgetter
from django.utils import timezone


class AllocationRequest(models.Model):

    show_private_fields = False

    STATUS_CHOICES = (
        ('N', 'N'),
        ('L', 'L'),
        ('A', 'A'),
        ('X', 'X'),
        ('R', 'R'),
        ('J', 'J'),
        ('E', 'E'),
    )

    INSTANCE_TYPE_CHOICES = (
        ('S', 'S'),
        ('X', 'X'),
        ('M', 'M'),
        ('L', 'L'),
        ('B', 'B'),
    )

    status = models.CharField(
        max_length=1, null=False, choices=STATUS_CHOICES, default='N')
    created_by = models.CharField(max_length=100, null=False)
    submit_date = models.DateField(null=False, default='2012-01-16')
    project_description = models.CharField(max_length=200, null=False)
    contact_email = models.CharField(max_length=75, null=False)
    start_date = models.DateField(null=False, default='2012-01-16')
    end_date = models.DateField(null=False, default='2012-01-16')
    primary_instance_type = models.CharField(
        max_length=1, null=False, choices=INSTANCE_TYPE_CHOICES, default='S')
    cores = models.IntegerField(null=False, default=1)
    core_hours = models.IntegerField(null=False, default=100)
    instances = models.IntegerField(null=False, default=1)
    use_case = models.TextField(null=False)
    usage_patterns = models.TextField(null=False)
    geographic_requirements = models.TextField(null=False)
    field_of_research_1 = models.CharField(max_length=6, null=True)
    for_percentage_1 = models.IntegerField(null=False, default=0)
    field_of_research_2 = models.CharField(max_length=6, null=True)
    for_percentage_2 = models.IntegerField(null=False, default=0)
    field_of_research_3 = models.CharField(max_length=6, null=True)
    for_percentage_3 = models.IntegerField(null=False, default=0)
    project_id = models.CharField(max_length=36, null=True)
    instance_quota = models.IntegerField(null=False, default=0)
    ram_quota = models.IntegerField(null=False, default=0)
    core_quota = models.IntegerField(null=False, default=0)
    project_name = models.CharField(max_length=100, null=True)
    status_explanation = models.CharField(max_length=200, null=True)
    volume_zone = models.CharField(max_length=64, null=True)
    object_storage_zone = models.CharField(max_length=64, null=True)
    approver_email = models.CharField(max_length=75, null=True)
    modified_time = models.DateTimeField(default=timezone.now, null=False)

    parent_request = models.ForeignKey('self', null=True)

    def __unicode__(self):
        return self.project_description + '(' + str(self.id) + ')'

    class Meta:
        ordering = ["project_description"]
        app_label = 'nectar_allocations'
        db_table = 'rcallocation_allocationrequest'
        managed = False if not settings.TEST_MODE else True

    # Refer to query for view view_institution_clean (Alan).
    @staticmethod
    def strip_email_sub_domains(domain):
        prefix = domain.split('.', 1)[0]
        if prefix in ('my', 'ems', 'exchange', 'groupwise',
                      'student', 'students', 'studentmail'):
            _, _, domain = domain.partition('.')
        if domain == 'griffithuni.edu.au':
            return 'griffith.edu.au'
        if domain == 'waimr.uwa.edu.au':
            return 'uwa.edu.au'
        if domain == 'uni.sydney.edu.au':
            return 'sydney.edu.au'
        if domain == 'usyd.edu.au':
            return 'sydney.edu.au'
        if domain == 'myune.edu.au':
            return 'une.edu.au'
        return domain

    @staticmethod
    def extract_email_domain(email_address):
        _, _, domain = email_address.partition('@')
        return domain

    @classmethod
    def find_active_allocations(cls):
        """Find the list of approved allocations.

        Find all, group them by name,
        but then return just the latest in each allocation group.
        The data needs some cleanup as there are some allocations
        with very similar names.
        """
        all_approved_allocations = cls \
            .objects.filter(Q(status='A') | Q(status='X')) \
            .exclude(field_of_research_1=None, field_of_research_2=None, field_of_research_3=None) \
            .order_by('-modified_time')
        seen = set()
        keep = []
        for allocation in all_approved_allocations:
            if allocation.project_description not in seen:
                keep.append(allocation)
                seen.add(allocation.project_description)
        return keep

    @staticmethod
    def is_valid_for_code(potential_for_code):
        return potential_for_code is not None

    """ The most fine-grained field-of-research code
    looks like 6 digits: '987654'

    The more general FOR codes for this field-of-research
    would be the leading  4 (= '9876') and 2 (= '98') digits.
    """
    @staticmethod
    def apply_for_code_to_summary(allocation_summary, code):
        allocation_summary['for_2'] = code[:2]
        allocation_summary['for_4'] = code[:4]
        allocation_summary['for_6'] = code[:6]

    def apply_partitioned_quotas(self, allocation_summary, percentage):
        fraction = float(percentage) / 100.0
        allocation_summary['instance_quota'] = self.instance_quota * fraction
        allocation_summary['core_quota'] = self.core_quota * fraction

    def summary(self, code):
        allocation_summary = dict()
        allocation_summary['id'] = self.id
        allocation_summary['institution'] = \
            self.institution_from_email(self.contact_email)
        allocation_summary['project_description'] = \
            self.project_description
        # Redact any email addresses.
        if self.show_private_fields:
            allocation_summary['usage_patterns'] = \
                self.apply_privacy_policy(self.usage_patterns)
        # Redact any email addresses.
        if self.show_private_fields:
            allocation_summary['use_case'] = \
                self.apply_privacy_policy(self.use_case)
        self.apply_for_code_to_summary(allocation_summary, code)
        if code == self.field_of_research_1:
            self.apply_partitioned_quotas(
                allocation_summary,
                self.for_percentage_1)
        elif code == self.field_of_research_2:
            self.apply_partitioned_quotas(
                allocation_summary,
                self.for_percentage_2)
        elif code == self.field_of_research_3:
            self.apply_partitioned_quotas(
                allocation_summary,
                self.for_percentage_3)
        return allocation_summary

    @classmethod
    def institution_from_email(cls, contact_email):
        email_domain = cls.extract_email_domain(contact_email)
        domain = cls.strip_email_sub_domains(email_domain)
        return domain

    # See: http://www.regular-expressions.info/email.html
    # Ignore case as only [A-Z] character class is specified.
    EMAIL_ADDRESS_REGEX = re.compile(
        r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b', re.IGNORECASE)
    REPLACEMENT = r'[XXXX]'

    @classmethod
    def redact_all_emails(cls, description):
        redacted_description = cls.EMAIL_ADDRESS_REGEX.sub(
            cls.REPLACEMENT, description)
        return redacted_description

    @classmethod
    def apply_privacy_policy(cls, description):
        redacted_description = cls.redact_all_emails(description)
        return redacted_description

    @classmethod
    def partition_active_allocations(cls):
        allocation_summaries = list()
        active_allocations = cls.find_active_allocations()
        for active_allocation in active_allocations:
            code = active_allocation.field_of_research_1
            if cls.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
            code = active_allocation.field_of_research_2
            if cls.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
            code = active_allocation.field_of_research_3
            if cls.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
        return allocation_summaries

    @classmethod
    def organise_allocations_tree(cls):
        allocations = cls.partition_active_allocations()
        allocations_tree = dict()

        for allocation in allocations:
            allocation_code_2 = allocation['for_2']
            if allocation_code_2 not in allocations_tree:
                allocations_tree[allocation_code_2] = dict()
            branch_major = allocations_tree[allocation_code_2]
            allocation_code_4 = allocation['for_4']
            if allocation_code_4 not in branch_major:
                branch_major[allocation_code_4] = dict()
            branch_minor = branch_major[allocation_code_4]
            allocation_code_6 = allocation['for_6']
            if allocation_code_6 not in branch_minor:
                branch_minor[allocation_code_6] = list()
            twig = dict()
            twig['id'] = allocation['id']
            twig['projectDescription'] = allocation['project_description']
            twig['institution'] = allocation['institution']
            if cls.show_private_fields:
                twig['useCase'] = allocation['use_case']
            if cls.show_private_fields:
                twig['usagePatterns'] = allocation['usage_patterns']
            twig['instanceQuota'] = allocation['instance_quota']
            twig['coreQuota'] = allocation['core_quota']
            branch_minor[allocation_code_6].append(twig)

        return allocations_tree

    @staticmethod
    def create_allocation_tree_branch_node(name):
        return {'name': name, 'children': []}

    @classmethod
    def create_allocation_tree_leaf_node(cls, allocation_summary):
        allocation_items = {
            'id': allocation_summary['id'],
            'name': allocation_summary['projectDescription'],
            'institution': allocation_summary['institution'],
            'instanceQuota': allocation_summary['instanceQuota'],
            'coreQuota': allocation_summary['coreQuota']
        }
        if cls.show_private_fields:
            allocation_items['useCase'] = \
                allocation_summary['useCase']
        if cls.show_private_fields:
            allocation_items['usagePatterns'] = \
                allocation_summary['usagePatterns']
        return allocation_items

    @classmethod
    def restructure_allocations_tree(cls):
        allocations_tree = cls.organise_allocations_tree()
        restructured_tree = \
            cls.create_allocation_tree_branch_node('allocations')
        cls.traverse_allocations_tree(allocations_tree, restructured_tree, 0)
        return restructured_tree

    @classmethod
    def traverse_allocations_tree(
            cls, allocations_tree,
            node_parent,
            recursion_depth):
        MAX_RECURSION_DEPTH = 2
        for node_name in allocations_tree.keys():
            node_children = cls.create_allocation_tree_branch_node(node_name)
            node_parent['children'].append(node_children)
            allocations_subtree = allocations_tree[node_name]
            if recursion_depth < MAX_RECURSION_DEPTH:
                cls.traverse_allocations_tree(
                    allocations_subtree, node_children, recursion_depth + 1)
            else:
                for allocation_summary in allocations_subtree:
                    allocation_items = \
                        cls.create_allocation_tree_leaf_node(
                            allocation_summary)
                    node_children['children'].append(allocation_items)

    @classmethod
    def get_all_for_project(cls, request_id):
        base_request = cls.objects.get(pk=request_id)
        project_summary = list()
        project_record = cls.__project_summary_record(base_request)
        project_summary.append(project_record)
        other_requests = cls.objects \
            .filter(project_description=base_request.project_description) \
            .exclude(id=request_id)
        for other_request in other_requests:
            project_record = cls.__project_summary_record(other_request)
            project_summary.append(project_record)
            project_summary.sort(key=itemgetter('modified_time'))
        return project_summary

    @classmethod
    def project_from_request_id(cls, request_id):
        allocations = cls.get_all_for_project(request_id)
        project_summary = allocations[-1]
        return project_summary

    @classmethod
    def __project_summary_record(cls, request):
        project_record = {
            'id': request.id,
            'project_description': request.project_description,
            'project_id': request.project_id,
            'institution': cls.institution_from_email(request.contact_email),
            'start_date': request.start_date.strftime('%Y-%m-%d'),
            'end_date': request.end_date.strftime('%Y-%m-%d'),
            'instance_quota': request.instance_quota,
            'core_quota': request.core_quota,
            'instances': request.instances,
            'cores': request.cores,
            'field_of_research_1': request.field_of_research_1,
            'for_percentage_1': request.for_percentage_1,
            'field_of_research_2': request.field_of_research_2,
            'for_percentage_2': request.for_percentage_2,
            'field_of_research_3': request.field_of_research_3,
            'for_percentage_3': request.for_percentage_3,
            'submit_date': request.submit_date.strftime('%Y-%m-%d'),
            'modified_time': request.modified_time.strftime(
                '%Y-%m-%d %H:%M:%S')
        }
        # Redact any email addresses.
        if cls.show_private_fields:
            project_record['use_case'] = \
                cls.apply_privacy_policy(request.use_case)
        # Redact any email addresses.
        if cls.show_private_fields:
            project_record['usage_patterns'] = \
                cls.apply_privacy_policy(request.usage_patterns)

        return project_record
