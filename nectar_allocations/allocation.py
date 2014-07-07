from django.db import models

# class Allocation(models.Model):
# 
#     core_quota = models.FloatField(db_column="core_hours", null=False)
#     for_2 = models.CharField(max_length=2, db_column="for_2", null=False)
#     for_4 = models.CharField(max_length=4, db_column="for_4", null=False),
#     for_6 = models.CharField(max_length=6, db_column="for_6", null=False),
#     instance_quota = models.FloatField(db_column="instance_quota", null=False)
#     institution = models.CharField(max_length=64, db_column="institution", null=False)
#     project_name = models.CharField(max_length=64, db_column="project_name", null=False)
#     usage_patterns = models.TextField(db_column="usage_patterns")
#     use_case = models.TextField(db_column="use_case")
# 
#     def __unicode__(self):
#         return self.project_name + '(' + self.id + ')'
#     
# class Meta:
#         ordering = ["project_name"]
#         app_label = 'nectar_allocations'
#         db_table = 'allocations_tb'
        

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
    modified_time = models.DateField(db_column="modified_time", null=False)
    
    parent_request = models.ForeignKey('self', db_column="parent_request_id")
    
    def __unicode__(self):
        return self.project_name + '(' + self.id + ')'
    
    class Meta:
        ordering = ["project_name"]
        app_label = 'nectar_allocations'
        db_table = 'rcallocation_allocationrequest'
        managed = True

