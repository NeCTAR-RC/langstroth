from django.db import models
from django.conf import settings

class ForCode(models.Model):

    code = models.CharField(max_length=6, primary_key=True, db_column="FOR_CODE")
    name = models.CharField(max_length=111, db_column="title")

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["code"]
        app_label = 'nectar_allocations'
        db_table = 'FOR_CODES'

    @staticmethod
    def code_dict():
        pairs = ForCode.objects.all()
        code_map = {}
        for pair in pairs:
            key = pair.code
            value = pair.name
            code_map[key] = value
        return code_map
