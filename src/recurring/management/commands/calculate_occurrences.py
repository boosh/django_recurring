from django.core.management.base import BaseCommand
from recurring.models import CalendarEntry


class Command(BaseCommand):
    help = (
        "Recalculates first/next/last, etc occurrence fields for all calendar entries"
    )

    def handle(self, *args, **options):
        calendar_entries = CalendarEntry.objects.all()
        total = calendar_entries.count()

        self.stdout.write(f"Recalculating occurrences for {total} calendar entries...")

        for i, calendar_entry in enumerate(calendar_entries, 1):
            calendar_entry.calculate_occurrences()
            self.stdout.write(f"Processed {i}/{total}: {calendar_entry.name}")

        self.stdout.write(
            self.style.SUCCESS("Successfully recalculated all occurrences")
        )
