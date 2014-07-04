from django.db import models

class ForCode(models.Model):
    
    code = models.CharField(max_length=6, primary_key=True, db_column="FOR_CODE")
    name = models.CharField(max_length=111, db_column="title")
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["code"]
        app_label = 'nectar_allocations'
        db_table = 'FOR_CODES'
        
    def map_all(self):
        return {}
    
