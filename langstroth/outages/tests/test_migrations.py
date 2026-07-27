from importlib import import_module

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

migration_0008 = import_module(
    'langstroth.outages.migrations.0008_rename_outage_to_announcement'
)


class RenamePermissionsTests(TestCase):
    """Cover the auth.Permission remap in migration 0008.

    On a fresh database the RunPython is a no-op (permissions are only
    created by post_migrate, after all migrations ran), so the full
    migration chain in CI never exercises the upgrade path: a database
    that already holds `add_outage`-style permissions granted to the
    `outage_managers` group. Simulate that state directly and run the
    remap against the real Permission model.
    """

    def setUp(self):
        # The renamed model's content type as it looks mid-upgrade
        # (RenameModel has already updated the `model` field).
        self.content_type = ContentType.objects.get(
            app_label='outages', model='announcement'
        )
        self.group = Group.objects.get_or_create(name='outage_managers')[0]

    def _make_legacy_permission(self):
        # Post-migrate has already created the new-codename permissions
        # in the test database; remove one to recreate the pre-remap
        # state where only the old codename exists.
        Permission.objects.filter(
            content_type=self.content_type, codename='add_announcement'
        ).delete()
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
            self.group.permissions.filter(codename='add_announcement').exists()
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

    def test_fresh_database_permissions_use_new_codenames(self):
        # post_migrate created the standard permissions from the
        # renamed models: new codenames present, old ones absent.
        codenames = set(
            Permission.objects.filter(
                content_type__app_label='outages'
            ).values_list('codename', flat=True)
        )
        self.assertIn('add_announcement', codenames)
        self.assertIn('view_announcementupdate', codenames)
        self.assertNotIn('add_outage', codenames)
