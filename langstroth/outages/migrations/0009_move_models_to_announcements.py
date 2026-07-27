# First half of the outages -> announcements app rename.
#
# Remove the models from this app's migration STATE only -- the tables
# stay in place and are adopted (and renamed) by the announcements
# app's 0001_initial, which depends on this migration. This app then
# remains as a migrations-only stub so existing databases and fresh
# installs share one migration history; it can be deleted (leaving
# harmless orphan django_migrations rows) once the rename release has
# been deployed everywhere.

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
