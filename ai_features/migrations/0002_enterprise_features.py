from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_features', '0001_initial'),
        ('accounts', '0001_initial'),
        ('candidates', '0003_certification'),
        ('jobs', '0002_job_new_fields'),
        ('interviews', '0004_enterprise_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumeanalysis',
            name='ats_score',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='ats_confidence',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='resume_strength',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='missing_keywords',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='weak_keywords',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='recommended_keywords',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='resumeanalysis',
            name='improvement_suggestions',
            field=models.JSONField(default=list),
        ),
        migrations.CreateModel(
            name='ChatHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=20)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_history', to='candidates.candidateprofile')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.CreateModel(
            name='VoiceInterviewSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('frontend', 'Frontend Developer'), ('backend', 'Backend Developer'), ('fullstack', 'Full Stack Developer'), ('java', 'Java Developer'), ('python', 'Python Developer'), ('hr', 'HR Interview'), ('custom', 'Custom Role')], default='custom', max_length=30)),
                ('custom_role', models.CharField(blank=True, max_length=100)),
                ('difficulty', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='intermediate', max_length=20)),
                ('questions', models.JSONField(default=list)),
                ('answers', models.JSONField(default=list)),
                ('evaluations', models.JSONField(default=list)),
                ('overall_score', models.FloatField(default=0)),
                ('technical_score', models.FloatField(default=0)),
                ('communication_score', models.FloatField(default=0)),
                ('confidence_score', models.FloatField(default=0)),
                ('readiness_score', models.FloatField(default=0)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voice_sessions', to='candidates.candidateprofile')),
            ],
        ),
        migrations.CreateModel(
            name='TalentPool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('contacted', models.BooleanField(default=False)),
                ('contacted_at', models.DateTimeField(blank=True, null=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('recruiter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talent_pool', to='accounts.user')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talent_pool_entries', to='candidates.candidateprofile')),
            ],
            options={'unique_together': {('recruiter', 'candidate')}},
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(choices=[('new_application', 'New Application'), ('assessment_submission', 'Assessment Submission'), ('interview_scheduled', 'Interview Scheduled'), ('interview_completed', 'Interview Completed'), ('offer_sent', 'Offer Sent'), ('offer_accepted', 'Offer Accepted'), ('offer_rejected', 'Offer Rejected'), ('reschedule_request', 'Reschedule Request'), ('reschedule_approved', 'Reschedule Approved'), ('reschedule_rejected', 'Reschedule Rejected')], max_length=40)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='accounts.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OfferResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.CharField(choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')], max_length=10)),
                ('remarks', models.TextField(blank=True)),
                ('responded_at', models.DateTimeField(auto_now_add=True)),
                ('decision', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='offer_response', to='interviews.candidatedecision')),
            ],
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(choices=[('profile_viewed', 'Profile Viewed'), ('job_applied', 'Job Applied'), ('assessment_started', 'Assessment Started'), ('assessment_completed', 'Assessment Completed'), ('interview_scheduled', 'Interview Scheduled'), ('interview_attended', 'Interview Attended'), ('offer_viewed', 'Offer Viewed'), ('offer_accepted', 'Offer Accepted'), ('offer_rejected', 'Offer Rejected')], max_length=40)),
                ('description', models.TextField(blank=True)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='candidates.candidateprofile')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=200)),
                ('model_name', models.CharField(blank=True, max_length=100)),
                ('object_id', models.CharField(blank=True, max_length=50)),
                ('changes', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
