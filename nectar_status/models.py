from django.db import models

class ForCode(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["code"]
    
