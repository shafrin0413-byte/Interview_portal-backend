from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='work_mode',
            field=models.CharField(choices=[('on-site', 'On-Site'), ('remote', 'Remote'), ('hybrid', 'Hybrid')], default='on-site', max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='job_type',
            field=models.CharField(choices=[('full-time', 'Full-Time'), ('part-time', 'Part-Time'), ('contract', 'Contract'), ('internship', 'Internship')], default='full-time', max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='experience',
            field=models.CharField(choices=[('fresher', 'Fresher'), ('1-2', '1-2 Years'), ('3-5', '3-5 Years'), ('5+', '5+ Years')], default='fresher', max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='salary',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
