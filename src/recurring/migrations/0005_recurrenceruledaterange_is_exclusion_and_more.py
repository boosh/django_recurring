# Generated by Django 5.1.1 on 2024-09-29 10:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recurring", "0004_remove_recurrencerule_end_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="recurrenceruledaterange",
            name="is_exclusion",
            field=models.BooleanField(
                default=False, help_text="Whether this date range is an exclusion"
            ),
        ),
        migrations.DeleteModel(
            name="RecurrenceDate",
        ),
    ]
