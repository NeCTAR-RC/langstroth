# Rename the Outage/OutageUpdate models to
# Announcement/AnnouncementUpdate.
#
# RenameModel renames the DB tables and (via the contenttypes app's
# injected RenameContentType operation) the django_content_type rows,
# but Django does NOT rename auth Permission rows.  Without the
# RunPython below, the permissions granted to the 'outage_managers'
# group (see 0002) would keep the old codenames while post_migrate's
# create_permissions() adds a fresh, ungranted set under the new
# codenames -- silently locking staff out of the admin.
#
# Constants are hardcoded rather than imported from models.py so this
# migration keeps describing the state at the time it was written.

from django.db import migrations

# (old codename, new codename, new human-readable name)
_PERMISSION_RENAMES = [
    ('add_outage', 'add_announcement', 'Can add announcement'),
    ('change_outage', 'change_announcement', 'Can change announcement'),
    ('delete_outage', 'delete_announcement', 'Can delete announcement'),
    ('view_outage', 'view_announcement', 'Can view announcement'),
    (
        'add_outageupdate',
        'add_announcementupdate',
        'Can add announcement update',
    ),
    (
        'change_outageupdate',
        'change_announcementupdate',
        'Can change announcement update',
    ),
    (
        'delete_outageupdate',
        'delete_announcementupdate',
        'Can delete announcement update',
    ),
    (
        'view_outageupdate',
        'view_announcementupdate',
        'Can view announcement update',
    ),
]


def _rename(permission_model, renames):
    # Idempotent: rows already carrying the new codename don't match the
    # filter.  On a fresh database no Permission rows exist yet (they
    # are created by post_migrate at the end of the migrate run), so
    # this is a no-op there.
    for old_codename, new_codename, new_name in renames:
        permission_model.objects.filter(
            content_type__app_label='outages', codename=old_codename
        ).update(codename=new_codename, name=new_name)


def rename_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    _rename(Permission, _PERMISSION_RENAMES)


def revert_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    old_names = {
        'add_outage': 'Can add outage',
        'change_outage': 'Can change outage',
        'delete_outage': 'Can delete outage',
        'view_outage': 'Can view outage',
        'add_outageupdate': 'Can add outage update',
        'change_outageupdate': 'Can change outage update',
        'delete_outageupdate': 'Can delete outage update',
        'view_outageupdate': 'Can view outage update',
    }
    reverse_renames = [
        (new, old, old_names[old]) for old, new, _ in _PERMISSION_RENAMES
    ]
    _rename(Permission, reverse_renames)


class Migration(migrations.Migration):
    dependencies = [
        ('outages', '0007_remove_scheduled_fields'),
    ]

    operations = [
        migrations.RenameModel('Outage', 'Announcement'),
        migrations.RenameModel('OutageUpdate', 'AnnouncementUpdate'),
        migrations.RunPython(rename_permissions, revert_permissions),
    ]
