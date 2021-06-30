from django.contrib import admin
from django.contrib.auth.models import Group

from langstroth.outages import models


class UpdateInline(admin.TabularInline):
    model = models.OutageUpdate
    extra = 0
    readonly_fields = ('created_by', 'modified_by', 'modification_time')


@admin.register(models.Outage)
class OutageAdmin(admin.ModelAdmin):
    list_display = ('summary', )
    inlines = (UpdateInline, )
    readonly_fields = ('created_by', 'modified_by', 'modification_time')

    @admin.display(description='summary')
    def summary(self, outage):
        return f"{outage.id}: {outage.title}"

    def save_model(self, request, obj, form, change):
        if change:
            if form.has_changed():
                obj.modified_by = request.user
        else:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for subform in formset.forms:
            if subform.instance.id is None:
                subform.instance.created_by = request.user
            elif subform.has_changed():
                subform.instance.modified_by = request.user
        super().save_formset(request, form, formset, change)


def get_outage_manager_group():
    return Group.objects.get(name='outage_managers')
