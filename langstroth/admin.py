from django.contrib import admin
from langstroth import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    pass
