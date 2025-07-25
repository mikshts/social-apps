# Generated by Django 5.2 on 2025-05-18 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_profile_birthday'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('gay', 'Gay'), ('lesbian', 'Lesbian'), ('neutral', 'Neutral')], max_length=10),
        ),
        migrations.AlterField(
            model_name='profile',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True),
        ),
    ]
