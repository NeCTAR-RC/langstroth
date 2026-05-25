from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            'outages',
            '0004_alter_outage_options_remove_outage_deleted_and_more',
        ),
    ]

    operations = [
        migrations.AddField(
            model_name='outage',
            name='start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='outage',
            name='end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='outage',
            name='planned_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='outage',
            name='severity',
            field=models.IntegerField(
                choices=[(1, 'Minimal'), (2, 'Significant'), (3, 'Severe')],
                default=2,
            ),
        ),
    ]
