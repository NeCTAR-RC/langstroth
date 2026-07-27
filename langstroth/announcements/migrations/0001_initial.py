# Second half of the outages -> announcements app rename.
#
# The models were removed from the outages app's migration STATE by
# outages/0009 (tables left in place). Here the announcements app
# adopts them:
#
#   * CreateModel runs as a state-only operation (the model definitions
#     mirror the outages app state after its 0008 rename);
#   * the tables are renamed outages_* -> announcements_* with plain
#     ALTER TABLE ... RENAME TO (works on MariaDB and the SQLite dev
#     database alike; MariaDB keeps the old index/constraint names,
#     which is cosmetic only. Note MariaDB DDL is not transactional,
#     so a failure between the two renames would need a manual rename
#     to recover -- the window is two metadata-only statements);
#   * the django_content_type rows move to the new app_label IN PLACE
#     (same primary keys), so auth_permission rows -- including the
#     outage_managers group grants remapped in outages/0008 -- follow
#     automatically and post_migrate's create_permissions() finds them
#     already present.
#
# On a fresh database the outages chain builds the tables first, so
# the renames and the content-type update behave identically there.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def update_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    # No-op on fresh databases: content types are only created by
    # post_migrate, after all migrations have run.
    ContentType.objects.filter(app_label='outages').update(
        app_label='announcements'
    )


def revert_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(app_label='announcements').update(
        app_label='outages'
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('outages', '0009_move_models_to_announcements'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Announcement',
                    fields=[
                        (
                            'id',
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name='ID',
                            ),
                        ),
                        ('title', models.CharField(max_length=255)),
                        ('description', models.TextField()),
                        ('start', models.DateTimeField()),
                        (
                            'planned_end',
                            models.DateTimeField(blank=True, null=True),
                        ),
                        ('end', models.DateTimeField(blank=True, null=True)),
                        (
                            'severity',
                            models.IntegerField(
                                choices=[
                                    (1, 'Minimal'),
                                    (2, 'Significant'),
                                    (3, 'Severe'),
                                ],
                                default=2,
                            ),
                        ),
                        (
                            'scheduled',
                            models.BooleanField(
                                blank=True, default=False, editable=False
                            ),
                        ),
                        (
                            'cancelled',
                            models.BooleanField(blank=True, default=False),
                        ),
                        (
                            'modification_time',
                            models.DateTimeField(auto_now=True),
                        ),
                        (
                            'created_by',
                            models.ForeignKey(
                                editable=False,
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name='+',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            'modified_by',
                            models.ForeignKey(
                                editable=False,
                                null=True,
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name='+',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        'ordering': ['-modification_time'],
                    },
                ),
                migrations.CreateModel(
                    name='AnnouncementUpdate',
                    fields=[
                        (
                            'id',
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name='ID',
                            ),
                        ),
                        ('time', models.DateTimeField()),
                        (
                            'modification_time',
                            models.DateTimeField(auto_now=True),
                        ),
                        (
                            'status',
                            models.CharField(
                                choices=[
                                    ('IN', 'Investigating'),
                                    ('ID', 'Identified'),
                                    ('P', 'Progressing'),
                                    ('F', 'Fixed'),
                                    ('R', 'Resolved'),
                                ],
                                max_length=2,
                            ),
                        ),
                        ('content', models.TextField()),
                        (
                            'created_by',
                            models.ForeignKey(
                                editable=False,
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name='+',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            'modified_by',
                            models.ForeignKey(
                                editable=False,
                                null=True,
                                on_delete=django.db.models.deletion.PROTECT,
                                related_name='+',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            'outage',
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='updates',
                                to='announcements.announcement',
                            ),
                        ),
                    ],
                    options={
                        'ordering': ['time', 'pk'],
                    },
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE outages_announcement '
                        'RENAME TO announcements_announcement'
                    ),
                    reverse_sql=(
                        'ALTER TABLE announcements_announcement '
                        'RENAME TO outages_announcement'
                    ),
                ),
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE outages_announcementupdate '
                        'RENAME TO announcements_announcementupdate'
                    ),
                    reverse_sql=(
                        'ALTER TABLE announcements_announcementupdate '
                        'RENAME TO outages_announcementupdate'
                    ),
                ),
            ],
        ),
        migrations.RunPython(update_content_types, revert_content_types),
    ]
