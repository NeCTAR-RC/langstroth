from django.db import models
from django.conf import settings
from django.db.models import Q

from nectar_allocations.switch import Switch

class AllocationRequest(models.Model):

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

    status = models.CharField(max_length=1, db_column="status", null=False, choices=STATUS_CHOICES, default='N')
    created_by = models.CharField(max_length=100, db_column="created_by", null=False)
    submit_date = models.DateField(db_column="submit_date", null=False, default='2012-01-16')
    project_name = models.CharField(max_length=200, db_column="project_name", null=False)
    contact_email = models.CharField(max_length=75, db_column="contact_email", null=False)
    start_date = models.DateField(db_column="start_date", null=False, default='2012-01-16')
    end_date = models.DateField(db_column="end_date", null=False, default='2012-01-16')
    primary_instance_type = models.CharField(max_length=1, db_column="primary_instance_type", null=False, choices=INSTANCE_TYPE_CHOICES, default='S')
    cores = models.IntegerField(db_column="cores", null=False, default=1)
    core_hours = models.IntegerField(db_column="core_hours", null=False, default=100)
    instances = models.IntegerField(db_column="instances", null=False, default=1)
    object_storage_GBs = models.IntegerField(db_column="object_storage_GBs", null=False, default=0)
    use_case = models.TextField(db_column="use_case", null=False)
    usage_patterns = models.TextField(db_column="usage_patterns", null=False)
    geographic_requirements = models.TextField(db_column="geographic_requirements", null=False)
    field_of_research_1 = models.CharField(max_length=6, db_column="field_of_research_1", null=True)
    for_percentage_1 = models.IntegerField(db_column="for_percentage_1", null=False, default=0)
    field_of_research_2 = models.CharField(max_length=6, db_column="field_of_research_2", null=True)
    for_percentage_2 = models.IntegerField(db_column="for_percentage_2", null=False, default=0)
    field_of_research_3 = models.CharField(max_length=6, db_column="field_of_research_3", null=True)
    for_percentage_3 = models.IntegerField(db_column="for_percentage_3", null=False, default=0)
    tenant_uuid = models.CharField(max_length=36, db_column="tenant_uuid", null=True)
    instance_quota = models.IntegerField(db_column="instance_quota", null=False, default=0)
    ram_quota = models.IntegerField(db_column="ram_quota", null=False, default=0)
    core_quota = models.IntegerField(db_column="core_quota", null=False, default=0)
    tenant_name = models.CharField(max_length=100, db_column="tenant_name", null=True)
    status_explanation = models.CharField(max_length=200, db_column="status_explanation", null=True)
    volume_gb = models.IntegerField(db_column="volume_gb", null=False, default=0)
    volume_zone = models.CharField(max_length=64, db_column="volume_zone", null=True)
    object_storage_zone = models.CharField(max_length=64, db_column="object_storage_zone", null=True)
    volume_quota = models.IntegerField(db_column="volume_quota", null=False, default=0)
    approver_email = models.CharField(max_length=75, db_column="approver_email", null=True)
    modified_time = models.DateTimeField(db_column="modified_time", null=False)
    
    parent_request = models.ForeignKey('self', db_column="parent_request_id", null=True)
    
    def __unicode__(self):
        return self.project_name + '(' + self.id + ')'
    
    class Meta:
        ordering = ["project_name"]
        app_label = 'nectar_allocations'
        db_table = 'rcallocation_allocationrequest'
        managed = False if not settings.TEST_MODE else True

    # Refer to query for view view_institution_clean (Alan).
    @staticmethod
    def strip_email_group(email_domain):
        domain = email_domain
        if email_domain.startswith('student') \
            or email_domain.startswith('my.') \
            or email_domain.startswith('ems.') \
            or email_domain.startswith('exchange.') \
            or email_domain.startswith('groupwise.'):
            group, delimiter, domain = email_domain.partition('.')       
        for case in Switch(domain):
            if case('griffithuni.edu.au'):
                return 'griffith.edu.au'
            if case('waimr.uwa.edu.au'):
                return 'uwa.edu.au'
            if case('uni.sydney.edu.au'):
                return 'sydney.edu.au'
            if case('usyd.edu.au'):
                return 'sydney.edu.au'
            if case('myune.edu.au'):
                return 'une.edu.au'
            #if case(): # default, could also just omit condition or 'if True'
                # Do nothing to the domain
            return domain
        
    @staticmethod
    def extract_email_domain(email_address):
        name, delimiter, domain = email_address.partition('@')       
        return domain
    
    # Find the list of allocations that have been approved, 
    # group them by name,
    # but then return just the latest in each allocation group.
    # The data needs some cleanup as there are some allocations with very similar names.
    @staticmethod
    def find_active_allocations():
        all_approved_allocations = AllocationRequest.objects.filter(Q(status ='A') | Q(status ='X')).order_by('-modified_time')
        seen = set()
        keep = []
        for allocation in all_approved_allocations:
            if allocation.project_name not in seen:
                keep.append(allocation)
                seen.add(allocation.project_name)
        return keep      
    
    @staticmethod
    def is_valid_for_code(potential_for_code):
        return potential_for_code is not None
    
    @staticmethod
    def apply_for_code_to_summary(allocation_summary, code):
        allocation_summary['for_2'] = code[:2]
        allocation_summary['for_4'] = code[:4]
        allocation_summary['for_6'] = code[:6]
        
    def apply_partitioned_quotas(self, allocation_summary, percentage):
        fraction =  float(percentage) / 100.0
        allocation_summary['instance_quota'] = self.instance_quota * fraction
        allocation_summary['core_quota'] = self.core_quota * fraction
    
    def summary(self, code):
        allocation_summary = dict()
        allocation_summary['id'] = self.id
        allocation_summary['institution'] = AllocationRequest.institution_from_email(self.contact_email)
        allocation_summary['project_name'] = self.project_name
        allocation_summary['usage_patterns'] = self.usage_patterns
        #allocation_summary['use_case'] = self.use_case
        AllocationRequest.apply_for_code_to_summary(allocation_summary, code)
        if code == self.field_of_research_1:
            self.apply_partitioned_quotas(allocation_summary, self.for_percentage_1)
        elif code == self.field_of_research_2:
            self.apply_partitioned_quotas(allocation_summary, self.for_percentage_2)
        elif code == self.field_of_research_3:
            self.apply_partitioned_quotas(allocation_summary, self.for_percentage_3)
        return allocation_summary
    
    @staticmethod
    def institution_from_email(contact_email): 
        email_domain = AllocationRequest.extract_email_domain(contact_email)
        domain = AllocationRequest.strip_email_group(email_domain)
        return domain;
   

    @staticmethod
    def partition_active_allocations(): 
        allocation_summaries = list()
        active_allocations = AllocationRequest.find_active_allocations()  
        for active_allocation in active_allocations:
            code = active_allocation.field_of_research_1
            if AllocationRequest.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
            code = active_allocation.field_of_research_2
            if AllocationRequest.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
            code = active_allocation.field_of_research_3
            if AllocationRequest.is_valid_for_code(code):
                allocation_summaries.append(active_allocation.summary(code))
        return allocation_summaries
    
    @staticmethod
    def organise_allocations_tree():
        allocations = AllocationRequest.partition_active_allocations()
        allocations_tree = dict()
         
        for allocation in allocations:
            allocation_code_2 = allocation['for_2']
            if not allocation_code_2 in allocations_tree:
                allocations_tree[allocation_code_2] = dict()
            branch_major = allocations_tree[allocation_code_2]
            allocation_code_4 = allocation['for_4']
            if not allocation_code_4 in branch_major:
                branch_major[allocation_code_4] = dict()
            branch_minor = branch_major[allocation_code_4]
            allocation_code_6 = allocation['for_6']
            if not allocation_code_6 in branch_minor:
                branch_minor[allocation_code_6] = list()
            twig = dict()
            twig['id'] = allocation['id']
            twig['projectName'] = allocation['project_name']
            twig['institution'] = allocation['institution']
            #twig['useCase'] = allocation['use_case']
            twig['usagePatterns'] = allocation['usage_patterns']
            twig['instanceQuota'] = allocation['instance_quota']
            twig['coreQuota'] = allocation['core_quota']
            branch_minor[allocation_code_6].append(twig)
             
        return allocations_tree

    @staticmethod
    def restructure_allocations_tree():
        allocations_tree = AllocationRequest.organise_allocations_tree();
        restructured_tree = dict()
        restructured_tree['name'] = 'allocations'
        restructured_tree['children'] = list()
        
        for code2 in allocations_tree.keys():
            named_children_2 = dict()
            named_children_2['name'] = code2
            named_children_2['children'] = list()
            restructured_tree['children'].append(named_children_2)            
            for code4 in allocations_tree[code2].keys():
                named_children_4 = dict()
                named_children_4['name'] = code4
                named_children_4['children'] = list()            
                named_children_2['children'].append(named_children_4)            
                for code6 in allocations_tree[code2][code4].keys(): 
                    named_children_6 = dict()
                    named_children_6['name'] = code6
                    named_children_6['children'] = list()            
                    named_children_4['children'].append(named_children_6)            
                    allocation_summaries = allocations_tree[code2][code4][code6]
                    for allocation_summary in allocation_summaries:
                        allocation_items = dict()
                        allocation_items['id'] = allocation_summary['id']
                        allocation_items['name'] = allocation_summary['projectName']
                        allocation_items['institution'] = allocation_summary['institution']
                        #allocation_items['useCase'] = allocation_summary['useCase']
                        allocation_items['usagePatterns'] = allocation_summary['usagePatterns']
                        allocation_items['instanceQuota'] = allocation_summary['instanceQuota']
                        allocation_items['coreQuota'] = allocation_summary['coreQuota']
                        named_children_6['children'].append(allocation_items)            
        return restructured_tree

    @staticmethod
    def project_allocations_from_allocation_request_id(allocation_request_id):
        base_request = AllocationRequest.objects.get(pk=allocation_request_id)      
        project_summary = list()
        project_record = AllocationRequest.project_summary_record(base_request)
        project_summary.append(project_record)
        other_requests = AllocationRequest.objects \
            .filter(project_name = base_request.project_name) \
            .exclude(id = allocation_request_id)
        for other_request in other_requests:
            project_record = AllocationRequest.project_summary_record(other_request)
            project_summary.append(project_record)
            project_summary.sort(key=lambda project_record: project_record['modified_time'])
        return project_summary

    @staticmethod
    def project_from_allocation_request_id(allocation_request_id):
        allocations = AllocationRequest.project_allocations_from_allocation_request_id(allocation_request_id)
        project_summary = allocations[-1]
        return project_summary
    
    @staticmethod
    def project_summary_record(allocation_request):
        project_record = dict()
        project_record['id'] = allocation_request.id
        project_record['project_name'] = allocation_request.project_name
        project_record['institution'] = AllocationRequest.institution_from_email(allocation_request.contact_email)
        project_record['start_date'] = allocation_request.start_date.strftime('%Y-%m-%d')
        project_record['end_date'] = allocation_request.end_date.strftime('%Y-%m-%d')
        #project_record['use_case'] = allocation_request.use_case
        project_record['usage_patterns'] = allocation_request.usage_patterns
        project_record['instance_quota'] = allocation_request.instance_quota
        project_record['core_quota'] = allocation_request.core_quota
        project_record['instances'] = allocation_request.instances
        project_record['cores'] = allocation_request.cores
        project_record['field_of_research_1'] = allocation_request.field_of_research_1
        project_record['for_percentage_1'] = allocation_request.for_percentage_1
        project_record['field_of_research_2'] = allocation_request.field_of_research_2
        project_record['for_percentage_2'] = allocation_request.for_percentage_2
        project_record['field_of_research_3'] = allocation_request.field_of_research_3
        project_record['for_percentage_3'] = allocation_request.for_percentage_3
        project_record['submit_date'] = allocation_request.submit_date.strftime('%Y-%m-%d')
        project_record['modified_time'] = allocation_request.modified_time.strftime('%Y-%m-%d %H:%M:%S')
        return project_record

