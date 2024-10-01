# Generated by Django 5.1.1 on 2024-10-01 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recurring", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="recurrenceset",
            name="timezone",
        ),
        migrations.RemoveField(
            model_name="recurrencesetrule",
            name="recurrence_set",
        ),
        migrations.RemoveField(
            model_name="recurrencesetrule",
            name="recurrence_rule",
        ),
        migrations.RemoveField(
            model_name="recurrencerule",
            name="timezone",
        ),
        migrations.CreateModel(
            name="CalendarEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="The name of the calendar entry",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="A description of the calendar entry"
                    ),
                ),
                (
                    "next_occurrence",
                    models.DateTimeField(
                        blank=True,
                        help_text="The next occurrence of this calendar entry",
                        null=True,
                    ),
                ),
                (
                    "previous_occurrence",
                    models.DateTimeField(
                        blank=True,
                        help_text="The previous occurrence of this calendar entry",
                        null=True,
                    ),
                ),
                (
                    "timezone",
                    models.ForeignKey(
                        default=1,
                        help_text="The timezone for this calendar entry",
                        on_delete=django.db.models.deletion.SET_DEFAULT,
                        to="recurring.timezone",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                ("is_full_day", models.BooleanField(default=False)),
                (
                    "calendar_entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="recurring.calendarentry",
                    ),
                ),
                (
                    "recurrence_rule",
                    models.OneToOneField(
                        help_text="The recurrence rule",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="recurring.recurrencerule",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ExclusionDateRange",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "start_date",
                    models.DateTimeField(
                        help_text="The start date of the exclusion range"
                    ),
                ),
                (
                    "end_date",
                    models.DateTimeField(
                        help_text="The end date of the exclusion range"
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        help_text="The event this exclusion date range belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exclusions",
                        to="recurring.event",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="RecurrenceRuleDateRange",
        ),
    ]