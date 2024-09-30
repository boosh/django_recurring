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
