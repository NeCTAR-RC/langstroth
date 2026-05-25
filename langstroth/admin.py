from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from langstroth import models


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    # Inherit the proper add/change forms (hashed passwords, password
    # reset link, etc.) and expose the OIDC `sub` UUID alongside the
    # standard AbstractUser fields.
    fieldsets = DjangoUserAdmin.fieldsets + (('OIDC', {'fields': ('sub',)}),)
