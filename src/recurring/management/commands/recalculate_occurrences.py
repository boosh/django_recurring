from django.core.management.base import BaseCommand

from ...models import RecurrenceSet


class Command(BaseCommand):
    help = "Recalculates next and previous occurrences for all RecurrenceSets"

    def handle(self, *args, **options):
        recurrence_sets = RecurrenceSet.objects.all()
        total = recurrence_sets.count()

        self.stdout.write(f"Recalculating occurrences for {total} RecurrenceSets...")

        for i, recurrence_set in enumerate(recurrence_sets, 1):
            recurrence_set.recalculate_occurrences()
            self.stdout.write(f"Processed {i}/{total}: {recurrence_set.name}")

        self.stdout.write(
            self.style.SUCCESS("Successfully recalculated all occurrences")
        )
