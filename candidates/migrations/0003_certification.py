from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0002_candidateprofile_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Certification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('issuer', models.CharField(blank=True, max_length=200)),
                ('year', models.CharField(blank=True, max_length=10)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='candidates.candidateprofile')),
            ],
        ),
    ]
