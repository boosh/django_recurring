# Generated by Django 5.1.1 on 2024-09-30 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recurring", "0006_remove_recurrencerule_until_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recurrenceset",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="The name of the recurrence set",
                max_length=255,
                null=True,
            ),
        ),
    ]
