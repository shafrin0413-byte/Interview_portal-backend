from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0003_candidatedecision'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interview',
            name='status',
            field=models.CharField(
                choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('rescheduled', 'Rescheduled')],
                default='scheduled', max_length=20
            ),
        ),
        migrations.CreateModel(
            name='RescheduleRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_date', models.DateTimeField()),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('recruiter_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('interview', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reschedule_requests', to='interviews.interview')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('category', models.CharField(choices=[('hr', 'HR'), ('technical', 'Technical'), ('behavioral', 'Behavioral'), ('project', 'Project-Based')], default='technical', max_length=20)),
                ('tags', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_bank', to='accounts.user')),
            ],
        ),
    ]
