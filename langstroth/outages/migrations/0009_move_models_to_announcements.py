# First half of the outages -> announcements app rename.
#
# Remove the models from this app's migration STATE only -- the tables
# stay in place and are adopted (and renamed) by the announcements
# app's 0001_initial, which depends on this migration. This app then
# remains as a migrations-only stub so existing databases and fresh
# installs share one migration history.
#
# The stub must NOT simply be deleted later: announcements/0001
# declares a dependency on this migration, so removing the app makes
# MigrationLoader raise NodeNotFoundError on every migrate (and
# dropping the dependency instead would break fresh installs, whose
# tables are built by this app's chain). It stays until the migration
# history is squashed/reset as a whole. It is a single tiny package,
# so the carrying cost is negligible.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('outages', '0008_rename_outage_to_announcement'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Delete the dependent model first.
                migrations.DeleteModel('AnnouncementUpdate'),
                migrations.DeleteModel('Announcement'),
            ],
            database_operations=[],
        ),
    ]
