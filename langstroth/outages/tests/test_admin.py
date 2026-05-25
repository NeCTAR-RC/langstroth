from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from langstroth import models as auth_models
from langstroth.outages import admin
from langstroth.outages import models


def _make_outage(user, **overrides):
    defaults = {
        "title": "t",
        "description": "d",
        "start": timezone.now(),
        "severity": models.SIGNIFICANT,
        "created_by": user,
    }
    defaults.update(overrides)
    return models.Outage.objects.create(**defaults)


class OutageAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Group.objects.get_or_create(name='outage_managers')
        cls.user = auth_models.User.objects.create_user(
            'admin', email='admin@test.com', is_staff=True, is_superuser=True
        )
        cls.other = auth_models.User.objects.create_user(
            'other', email='other@test.com', is_staff=True
        )

    def setUp(self):
        self.site = AdminSite()
        self.outage_admin = admin.OutageAdmin(models.Outage, self.site)

    def test_summary(self):
        outage = models.Outage(id=42, title="Hi")
        self.assertEqual("42: Hi", self.outage_admin.summary(outage))

    def test_save_model_new(self):
        request = mock.Mock(user=self.user)
        outage = models.Outage(
            title="t",
            description="d",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
        )
        form = mock.Mock(has_changed=mock.Mock(return_value=False))
        self.outage_admin.save_model(request, outage, form, change=False)
        self.assertEqual(self.user, outage.created_by)

    def test_save_model_change_with_modification(self):
        outage = _make_outage(self.user)
        request = mock.Mock(user=self.other)
        form = mock.Mock(has_changed=mock.Mock(return_value=True))
        self.outage_admin.save_model(request, outage, form, change=True)
        self.assertEqual(self.other, outage.modified_by)

    def test_save_model_change_without_modification(self):
        outage = _make_outage(self.user)
        request = mock.Mock(user=self.other)
        form = mock.Mock(has_changed=mock.Mock(return_value=False))
        self.outage_admin.save_model(request, outage, form, change=True)
        self.assertIsNone(outage.modified_by)

    def test_save_formset_new_update(self):
        outage = _make_outage(self.user)
        new_sub = mock.Mock()
        new_sub.instance = models.OutageUpdate(
            outage=outage,
            status=models.INVESTIGATING,
            content="x",
        )
        new_sub.instance.id = None
        new_sub.has_changed = mock.Mock(return_value=True)

        existing_update = models.OutageUpdate.objects.create(
            outage=outage,
            time=outage.modification_time,
            status=models.INVESTIGATING,
            content="y",
            created_by=self.user,
        )
        changed_sub = mock.Mock()
        changed_sub.instance = existing_update
        changed_sub.has_changed = mock.Mock(return_value=True)

        formset = mock.Mock()
        formset.forms = [new_sub, changed_sub]
        formset.save = mock.Mock(return_value=[])
        formset.deleted_objects = []
        formset.new_objects = []
        formset.changed_objects = []
        request = mock.Mock(user=self.other)

        self.outage_admin.save_formset(
            request, mock.Mock(), formset, change=True
        )
        self.assertEqual(self.other, new_sub.instance.created_by)
        self.assertEqual(self.other, changed_sub.instance.modified_by)


class HelperTests(TestCase):
    def test_get_outage_manager_group(self):
        Group.objects.get_or_create(name='outage_managers')
        group = admin.get_outage_manager_group()
        self.assertEqual('outage_managers', group.name)
