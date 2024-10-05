====================
Management Commands
====================

django-recurring provides management commands to help you manage your calendar entries. These commands can be run from the command line and are useful for maintenance tasks and bulk operations.

calculate_occurrences
-----------------------

This command recalculates the `occurrence fields <https://django-recurring.readthedocs.io/en/latest/recurring.html#recurring.models.CalendarEntry.calculate_occurrences>`_ stored in CalendarEntry objects for all objects in the database.

Usage
^^^^^

To run the command, use the following:

.. code-block:: console

    $ python manage.py calculate_occurrences

This command will:

1. Fetch all CalendarEntry objects from the database.
2. For each one, call the `calculate_occurrences()` method.
3. Update the occurrence fields of each `CalendarEntry`.
4. Display progress information in the console.

When to Use
^^^^^^^^^^^

You should use this command in the following situations:

1. After bulk importing CalendarEntry instances from another source.
2. If you suspect that the occurrence fields are out of sync with the actual recurrence rules.
3. After making changes to the recurrence rules or dates outside of the normal save process (e.g., direct database modifications).

Example Output
^^^^^^^^^^^^^^

Here's an example of what you might see when running the command:

.. code-block:: console

    $ python manage.py calculate_occurrences
    Recalculating occurrences for 100 CalendarEntries...
    Processed 1/100: Weekly Team Meeting
    Processed 2/100: Monthly Board Meeting
    ...
    Processed 100/100: Annual Company Picnic
    Successfully recalculated all occurrences
