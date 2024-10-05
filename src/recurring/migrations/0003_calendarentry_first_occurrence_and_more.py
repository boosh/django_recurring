# Generated by Django 5.1.1 on 2024-10-05 08:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recurring", "0002_alter_calendarentry_description_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendarentry",
            name="first_occurrence",
            field=models.DateTimeField(
                blank=True,
                help_text="The first occurrence of this calendar entry",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="calendarentry",
            name="last_occurrence",
            field=models.DateTimeField(
                blank=True,
                help_text="The last occurrence of this calendar entry",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="calendarentry",
            name="description",
            field=models.TextField(
                blank=True, help_text="Will be used as the ical summary"
            ),
        ),
        migrations.AlterField(
            model_name="calendarentry",
            name="name",
            field=models.CharField(
                help_text="Will be used as the ical filename, slugified, and ical summary if no description is set",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="calendarentry",
            name="next_occurrence",
            field=models.DateTimeField(
                blank=True,
                help_text="The next occurrence of this calendar entry from the last time occurrences were calculated",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="calendarentry",
            name="previous_occurrence",
            field=models.DateTimeField(
                blank=True,
                help_text="The previous occurrence of this calendar entry from the last time occurrences were calculated",
                null=True,
            ),
        ),
    ]
