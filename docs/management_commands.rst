====================
Management Commands
====================

django-recurring provides management commands to help you manage your RecurrenceSets. These commands can be run from the command line and are useful for maintenance tasks and bulk operations.

recalculate_occurrences
-----------------------

This command recalculates the next and previous occurrences for all RecurrenceSets in the database.

Usage
^^^^^

To run the command, use the following:

.. code-block:: console

    $ python manage.py recalculate_occurrences

This command will:

1. Fetch all RecurrenceSets from the database.
2. For each RecurrenceSet, call the `recalculate_occurrences()` method.
3. Update the `next_occurrence` and `previous_occurrence` fields of each RecurrenceSet.
4. Display progress information in the console.

When to Use
^^^^^^^^^^^

You should use this command in the following situations:

1. After bulk importing RecurrenceSets from another source.
2. If you suspect that the `next_occurrence` and `previous_occurrence` fields are out of sync with the actual recurrence rules.
3. After making changes to the recurrence rules or dates outside of the normal save process (e.g., direct database modifications).

Example Output
^^^^^^^^^^^^^^

Here's an example of what you might see when running the command:

.. code-block:: console

    $ python manage.py recalculate_occurrences
    Recalculating occurrences for 100 RecurrenceSets...
    Processed 1/100: Weekly Team Meeting
    Processed 2/100: Monthly Board Meeting
    ...
    Processed 100/100: Annual Company Picnic
    Successfully recalculated all occurrences

Custom Management Commands
--------------------------

You can create your own custom management commands to perform other bulk operations on RecurrenceSets. Here's an example of how you might structure a custom command:

.. code-block:: python

    from django.core.management.base import BaseCommand
    from recurring.models import RecurrenceSet

    class Command(BaseCommand):
        help = 'Your custom command description'

        def handle(self, *args, **options):
            recurrence_sets = RecurrenceSet.objects.all()
            for recurrence_set in recurrence_sets:
                # Perform your custom operation here
                self.stdout.write(f"Processed: {recurrence_set.name}")

            self.stdout.write(self.style.SUCCESS('Custom command completed successfully'))

Save this in a file named `your_command_name.py` in the `management/commands/` directory of your Django app. You can then run it with:

.. code-block:: console

    $ python manage.py your_command_name

Remember to thoroughly test any custom commands before running them on production data.
