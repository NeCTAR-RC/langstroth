from importlib import import_module

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

migration_0008 = import_module(
    'langstroth.outages.migrations.0008_rename_outage_to_announcement'
)


class RenamePermissionsTests(TestCase):
    """Cover the auth.Permission remap in outages migration 0008.

    On a fresh database the RunPython is a no-op (permissions are only
    created by post_migrate, after all migrations ran), so the full
    migration chain in CI never exercises the upgrade path: a database
    that already holds `add_outage`-style permissions granted to the
    `outage_managers` group. Simulate that state directly and run the
    remap against the real Permission model.
    """

    def setUp(self):
        # Recreate the content type as it looked when 0008 ran
        # mid-upgrade: RenameModel had updated the `model` field, but
        # the app move to `announcements` had not yet happened.
        self.content_type = ContentType.objects.create(
            app_label='outages', model='announcement'
        )
        self.group = Group.objects.get_or_create(name='outage_managers')[0]

    def _make_legacy_permission(self):
        permission = Permission.objects.create(
            content_type=self.content_type,
            codename='add_outage',
            name='Can add outage',
        )
        self.group.permissions.add(permission)
        return permission

    def test_remap_renames_permission_and_keeps_group_grant(self):
        permission = self._make_legacy_permission()

        migration_0008._rename(Permission, migration_0008._PERMISSION_RENAMES)

        permission.refresh_from_db()
        self.assertEqual('add_announcement', permission.codename)
        self.assertEqual('Can add announcement', permission.name)
        self.assertTrue(
            self.group.permissions.filter(codename='add_announcement')
            .exclude(content_type__app_label='announcements')
            .exists()
        )

    def test_remap_is_idempotent(self):
        self._make_legacy_permission()

        migration_0008._rename(Permission, migration_0008._PERMISSION_RENAMES)
        migration_0008._rename(Permission, migration_0008._PERMISSION_RENAMES)

        self.assertEqual(
            1,
            Permission.objects.filter(
                content_type=self.content_type,
                codename='add_announcement',
            ).count(),
        )


class AppMoveTests(TestCase):
    """Assert the end state of the outages -> announcements app move.

    The test database is built by running the full migration chain, so
    these tests prove outages/0009 + announcements/0001 leave content
    types and permissions where the application expects them.
    """

    def test_content_types_moved_to_announcements(self):
        self.assertTrue(
            ContentType.objects.filter(
                app_label='announcements', model='announcement'
            ).exists()
        )
        self.assertTrue(
            ContentType.objects.filter(
                app_label='announcements', model='announcementupdate'
            ).exists()
        )
        self.assertFalse(
            ContentType.objects.filter(app_label='outages').exists()
        )

    def test_permissions_use_new_codenames_and_label(self):
        codenames = set(
            Permission.objects.filter(
                content_type__app_label='announcements'
            ).values_list('codename', flat=True)
        )
        self.assertIn('add_announcement', codenames)
        self.assertIn('view_announcementupdate', codenames)
        self.assertNotIn('add_outage', codenames)
        # No duplicate permission set survived under the old label.
        self.assertFalse(
            Permission.objects.filter(
                content_type__app_label='outages'
            ).exists()
        )
