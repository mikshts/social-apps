# Generated by Django 5.2 on 2025-06-25 08:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_message'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gender', models.JSONField(blank=True, default=list)),
                ('looking_for', models.JSONField(blank=True, default=list)),
                ('age_range', models.JSONField(blank=True, default=list)),
                ('goal', models.JSONField(blank=True, default=list)),
                ('meet', models.JSONField(blank=True, default=list)),
                ('smoke', models.JSONField(blank=True, default=list)),
                ('drink', models.JSONField(blank=True, default=list)),
                ('children', models.JSONField(blank=True, default=list)),
                ('hobbies', models.JSONField(blank=True, default=list)),
                ('traits', models.JSONField(blank=True, default=list)),
                ('love_language', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='survey', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
