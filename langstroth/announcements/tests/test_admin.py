from unittest import mock

from django.contrib.admin import site as admin_site
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


class VocabularyAdminTests(TestCase):
    """The admin is the only UI for managing the vocabularies, so make
    sure both are registered with the slug tooling operators need.
    """

    def test_vocabularies_registered_with_slug_tooling(self):
        for model in (models.Service, models.AvailabilityZone):
            self.assertTrue(admin_site.is_registered(model))
            model_admin = admin_site.get_model_admin(model)
            self.assertEqual(
                {'slug': ('name',)}, model_admin.prepopulated_fields
            )
            self.assertIn('slug', model_admin.list_display)
            self.assertIn('name', model_admin.search_fields)

    def test_announcement_admin_exposes_tags(self):
        model_admin = admin.AnnouncementAdmin(models.Announcement, AdminSite())
        self.assertEqual(
            ('services', 'availability_zones'), model_admin.filter_horizontal
        )
        self.assertIn('services', model_admin.list_filter)
        self.assertIn('availability_zones', model_admin.list_filter)


class AdminPageRenderTests(TestCase):
    """The admin is the de facto edit UI, so render the pages that
    carry the new widgets rather than trusting the system checks.
    """

    @classmethod
    def setUpTestData(cls):
        cls.superuser = auth_models.User.objects.create_user(
            'super', email='super@test.com', is_staff=True, is_superuser=True
        )
        cls.compute = models.Service.objects.create(
            name="Compute", slug="compute"
        )
        models.AvailabilityZone.objects.create(
            name="melbourne-qh2", slug="melbourne-qh2"
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_add_pages_render(self):
        for url in (
            '/admin/announcements/announcement/add/',
            '/admin/announcements/service/add/',
            '/admin/announcements/availabilityzone/add/',
        ):
            response = self.client.get(url)
            self.assertEqual(200, response.status_code, url)

    def test_change_page_shows_help_text_and_tags(self):
        outage = _make_outage(self.superuser)
        outage.services.add(self.compute)
        response = self.client.get(
            f'/admin/announcements/announcement/{outage.pk}/change/'
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(
            response, "Leave empty if this affects all services."
        )
        self.assertContains(
            response, "Leave empty if this affects all availability zones."
        )
        self.assertContains(response, "Compute")

    def test_changelist_offers_tag_filters(self):
        response = self.client.get('/admin/announcements/announcement/')
        self.assertEqual(200, response.status_code)
        # RelatedFieldListFilter lists every vocabulary term.
        self.assertContains(response, "Compute")
        self.assertContains(response, "melbourne-qh2")


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
