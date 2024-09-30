=====
Usage
=====

Quick Start
-----------

1. Add a RecurrenceSet to your model:

   .. code-block:: python

      from django.db import models
      from recurring.models import RecurrenceSet

      class Event(models.Model):
          name = models.CharField(max_length=200)
          recurrence = models.ForeignKey(RecurrenceSet, on_delete=models.CASCADE)

2. Create a RecurrenceSet with rules:

   .. code-block:: python

      from django.utils import timezone
      from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule

      # Create a RecurrenceSet
      recurrence_set = RecurrenceSet.objects.create(name="Weekly Meeting")

      # Create a rule
      rule = RecurrenceRule.objects.create(
          frequency=RecurrenceRule.Frequency.WEEKLY,
          interval=1,
          byweekday=[0]  # Monday
      )

      # Add a date range to the rule
      rule.date_ranges.create(
          start_date=timezone.now(),
          end_date=timezone.now() + timezone.timedelta(days=365)
      )

      # Associate the rule with the RecurrenceSet
      RecurrenceSetRule.objects.create(
          recurrence_set=recurrence_set,
          recurrence_rule=rule
      )

      # Recalculate occurrences
      recurrence_set.recalculate_occurrences()

3. Query previous/next events within a date range:

   .. code-block:: python

      events = Event.objects.filter(
          recurrence__next_occurrence__gte=timezone.now(),
          recurrence__previous_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
      )

Advanced Usage
--------------

Creating Complex Recurrence Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create complex recurrence patterns by combining multiple rules:

.. code-block:: python

   # Create a RecurrenceSet for a complex schedule
   recurrence_set = RecurrenceSet.objects.create(name="Complex Schedule")

   # Rule 1: Every Monday and Wednesday
   rule1 = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=[0, 2]  # Monday and Wednesday
   )

   # Rule 2: First Friday of every month
   rule2 = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.MONTHLY,
       interval=1,
       byweekday=[4],  # Friday
       bysetpos=[1]  # First occurrence
   )

   # Add rules to the RecurrenceSet
   RecurrenceSetRule.objects.create(recurrence_set=recurrence_set, recurrence_rule=rule1)
   RecurrenceSetRule.objects.create(recurrence_set=recurrence_set, recurrence_rule=rule2)

   # Set date ranges for both rules
   for rule in [rule1, rule2]:
       rule.date_ranges.create(
           start_date=timezone.now(),
           end_date=timezone.now() + timezone.timedelta(days=365)
       )

   recurrence_set.recalculate_occurrences()

Recalculating occurrences
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to query by the `next` and `previous` occurrence fields you may need to manually call `recalculate_occurrences()`. It is called when creating/deleting rules but it may be missing in some places.

You can call recalculate them in several ways:

.. code-block:: python

    recurrence_set.recalculate_occurrences()
    recurrence_set.save(recalculate=True)

Or you can recalculate them in bulk via the :doc:`management command <management_commands>`.

Exporting to iCal Format
~~~~~~~~~~~~~~~~~~~~~~~~

django-recurring supports exporting RecurrenceSets to iCal format:

.. code-block:: python

   # Assuming you have a RecurrenceSet object
   ical_string = recurrence_set.to_ical()

   # You can also specify a custom PRODID
   custom_ical_string = recurrence_set.to_ical(prod_id="-//My Company//My Product//EN")

   # Save the iCal string to a file
   with open('my_event.ics', 'w') as f:
       f.write(ical_string)

This will create an iCal file that can be imported into most calendar applications.

