from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('candidates', '0003_certification'),
        ('jobs', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResumeAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skills', models.JSONField(default=list)),
                ('education', models.JSONField(default=list)),
                ('experience', models.JSONField(default=list)),
                ('certifications', models.JSONField(default=list)),
                ('experience_years', models.FloatField(default=0)),
                ('analyzed_at', models.DateTimeField(auto_now=True)),
                ('candidate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='resume_analysis', to='candidates.candidateprofile')),
            ],
        ),
        migrations.CreateModel(
            name='JobMatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_percentage', models.FloatField(default=0)),
                ('matching_skills', models.JSONField(default=list)),
                ('missing_skills', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_matches', to='candidates.candidateprofile')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidate_matches', to='jobs.job')),
            ],
            options={'unique_together': {('candidate', 'job')}},
        ),
        migrations.CreateModel(
            name='CandidateRanking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField(default=0)),
                ('match_score', models.FloatField(default=0)),
                ('experience_score', models.FloatField(default=0)),
                ('certification_score', models.FloatField(default=0)),
                ('total_score', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rankings', to='candidates.candidateprofile')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rankings', to='jobs.job')),
            ],
            options={'ordering': ['rank'], 'unique_together': {('job', 'candidate')}},
        ),
        migrations.CreateModel(
            name='AIQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.CharField(max_length=200)),
                ('skills', models.JSONField(default=list)),
                ('experience_level', models.CharField(max_length=50)),
                ('questions', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_questions', to='accounts.user')),
            ],
        ),
    ]
