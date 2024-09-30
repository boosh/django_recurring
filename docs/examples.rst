========
Examples
========

This page provides various examples of how to use django-recurring in your Django projects.

Basic Weekly Recurrence
-----------------------

.. code-block:: python

   from django.utils import timezone
   from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule

   # Create a RecurrenceSet for weekly team meetings
   recurrence_set = RecurrenceSet.objects.create(name="Weekly Team Meeting")

   # Add a rule for every Monday
   rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=[0]  # Monday
   )

   # Set the date range for the entire year
   rule.date_ranges.create(
       start_date=timezone.now(),
       end_date=timezone.now() + timezone.timedelta(days=365)
   )

   # Link the rule to the RecurrenceSet
   RecurrenceSetRule.objects.create(
       recurrence_set=recurrence_set,
       recurrence_rule=rule
   )

   # Recalculate occurrences
   recurrence_set.recalculate_occurrences()

Monthly Recurrence on Specific Days
-----------------------------------

.. code-block:: python

   # Create a RecurrenceSet for monthly finance meetings
   recurrence_set = RecurrenceSet.objects.create(name="Monthly Finance Meeting")

   # Add a rule for the 15th of every month
   rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.MONTHLY,
       interval=1,
       bymonthday=[15]
   )

   # Set the date range for two years
   rule.date_ranges.create(
       start_date=timezone.now(),
       end_date=timezone.now() + timezone.timedelta(days=730)
   )

   RecurrenceSetRule.objects.create(
       recurrence_set=recurrence_set,
       recurrence_rule=rule
   )

   recurrence_set.recalculate_occurrences()

Complex Recurrence Pattern
--------------------------

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

   # Set date ranges for both rules
   for rule in [rule1, rule2]:
       rule.date_ranges.create(
           start_date=timezone.now(),
           end_date=timezone.now() + timezone.timedelta(days=365)
       )
       RecurrenceSetRule.objects.create(
           recurrence_set=recurrence_set,
           recurrence_rule=rule
       )

   recurrence_set.recalculate_occurrences()

Using RecurrenceSet in a Model
------------------------------

.. code-block:: python

   from django.db import models
   from recurring.models import RecurrenceSet

   class Event(models.Model):
       name = models.CharField(max_length=200)
       recurrence = models.ForeignKey(RecurrenceSet, on_delete=models.CASCADE)

   # Create an event with a recurrence pattern
   recurrence_set = RecurrenceSet.objects.create(name="Weekly Event")
   rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=[0]  # Monday
   )
   rule.date_ranges.create(
       start_date=timezone.now(),
       end_date=timezone.now() + timezone.timedelta(days=365)
   )
   RecurrenceSetRule.objects.create(
       recurrence_set=recurrence_set,
       recurrence_rule=rule
   )
   recurrence_set.recalculate_occurrences()

   event = Event.objects.create(name="Team Sync", recurrence=recurrence_set)

   # Query events within a date range
   events = Event.objects.filter(
       recurrence__next_occurrence__gte=timezone.now(),
       recurrence__previous_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
   )

Exporting to iCal Format
------------------------

django-recurring supports exporting RecurrenceSets to iCal format:

.. code-block:: python

   recurrence_set = RecurrenceSet.objects.get(name="Weekly Team Meeting")
   ical_string = recurrence_set.to_ical()

   # Optionally, you can specify a custom PRODID
   custom_ical_string = recurrence_set.to_ical(prod_id="-//My Company//My Product//EN")

   # You can then save this to a file or send it as a response
   with open('team_meeting.ics', 'w') as f:
       f.write(ical_string)

The resulting iCal file will contain all the recurrence rules and can be imported into most calendar applications.

.. important::

    See notes on :doc:`recalculating occurrences <usage>`
