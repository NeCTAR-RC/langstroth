from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('outages', '0006_populate_outage_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outage',
            name='scheduled_start',
        ),
        migrations.RemoveField(
            model_name='outage',
            name='scheduled_end',
        ),
        migrations.RemoveField(
            model_name='outage',
            name='scheduled_severity',
        ),
        migrations.RemoveField(
            model_name='outageupdate',
            name='severity',
        ),
        migrations.AlterField(
            model_name='outage',
            name='start',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='outage',
            name='scheduled',
            field=models.BooleanField(
                blank=True, default=False, editable=False
            ),
        ),
        migrations.AlterField(
            model_name='outageupdate',
            name='status',
            field=models.CharField(
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
    ]
