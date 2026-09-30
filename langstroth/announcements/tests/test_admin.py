from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from langstroth.announcements import admin
from langstroth.announcements import models
from langstroth import models as auth_models


def _make_outage(user, **overrides):
    defaults = {
        "title": "t",
        "description": "d",
        "start": timezone.now(),
        "severity": models.SIGNIFICANT,
        "created_by": user,
    }
    defaults.update(overrides)
    return models.Announcement.objects.create(**defaults)


class AnnouncementAdminTests(TestCase):
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
        self.outage_admin = admin.AnnouncementAdmin(
            models.Announcement, self.site
        )

    def test_summary(self):
        outage = models.Announcement(id=42, title="Hi")
        self.assertEqual("42: Hi", self.outage_admin.summary(outage))

    def test_save_model_new(self):
        request = mock.Mock(user=self.user)
        outage = models.Announcement(
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
        new_sub.instance = models.AnnouncementUpdate(
            outage=outage,
            status=models.INVESTIGATING,
            content="x",
        )
        new_sub.instance.id = None
        new_sub.has_changed = mock.Mock(return_value=True)

        existing_update = models.AnnouncementUpdate.objects.create(
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


class UpdateInlineNewsGuardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="inline", email="inline@test", is_superuser=True
        )

    def _inline(self):
        return admin.UpdateInline(models.Announcement, AdminSite())

    def test_no_add_rows_for_news(self):
        news = models.Announcement.objects.create(
            title="n",
            description="d",
            category=models.Category.NEWS,
            start=timezone.now(),
            severity=None,
            created_by=self.user,
        )
        request = mock.Mock(user=self.user)
        self.assertFalse(self._inline().has_add_permission(request, news))

    def test_add_rows_allowed_for_outages_and_add_page(self):
        outage = models.Announcement.objects.create(
            title="o",
            description="d",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        request = mock.Mock(user=self.user)
        self.assertTrue(self._inline().has_add_permission(request, outage))
        self.assertTrue(self._inline().has_add_permission(request, None))
