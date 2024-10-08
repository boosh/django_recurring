# Generated by Django 5.1.1 on 2024-10-08 05:30

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recurring", "0003_calendarentry_first_occurrence_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendarentry",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="calendarentry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]