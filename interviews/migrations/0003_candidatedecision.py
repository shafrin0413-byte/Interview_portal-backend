from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('interviews', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateDecision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision', models.CharField(choices=[('reject', 'Reject'), ('hold', 'Hold'), ('hire', 'Hire')], max_length=10)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('delivery_status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('interview', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='decision', to='interviews.interview')),
                ('sent_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decisions_sent', to='accounts.user')),
            ],
        ),
    ]
