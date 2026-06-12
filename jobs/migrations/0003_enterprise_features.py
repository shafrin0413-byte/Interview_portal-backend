from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_job_new_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(
                choices=[('open', 'Open'), ('closed', 'Closed'), ('draft', 'Draft'), ('expired', 'Expired')],
                default='open', max_length=10
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[('applied', 'Applied'), ('shortlisted', 'Shortlisted'), ('rejected', 'Rejected'), ('interview', 'Interview Scheduled'), ('hired', 'Hired'), ('on_hold', 'On Hold')],
                default='applied', max_length=20
            ),
        ),
    ]
