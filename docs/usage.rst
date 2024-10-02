=====
Usage
=====

Quick Start
-----------

1. Add a CalendarEntry to your model:

   .. code-block:: python

      from django.db import models
      from recurring.models import CalendarEntry

      class Meeting(models.Model):
          title = models.CharField(max_length=200)
          calendar_entry = models.ForeignKey(CalendarEntry, on_delete=models.CASCADE)

2. Create a CalendarEntry with events and recurrence rules:

   .. code-block:: python

      from django.utils import timezone
      from recurring.models import CalendarEntry, Event, RecurrenceRule, Timezone, MONDAY

      # Create a CalendarEntry
      calendar_entry = CalendarEntry.objects.create(
          name="Weekly Team Meeting",
          description="Regular team sync-up",
          timezone=Timezone.objects.get(name="UTC")
      )

      # Create an event with a recurrence rule
      rule = RecurrenceRule.objects.create(
          frequency=RecurrenceRule.Frequency.WEEKLY,
          interval=1,
          byweekday=[MONDAY]  # Every Monday
      )

      event = Event.objects.create(
          calendar_entry=calendar_entry,
          start_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0),
          end_time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0),
          recurrence_rule=rule
      )

      # Recalculate occurrences
      calendar_entry.recalculate_occurrences()

3. Query upcoming meetings:

   .. code-block:: python

      upcoming_meetings = Meeting.objects.filter(
          calendar_entry__next_occurrence__gte=timezone.now(),
          calendar_entry__next_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
      )

Advanced Usage
--------------

Creating Complex Recurrence Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create complex recurrence patterns by combining multiple events with different rules:

.. code-block:: python

   # Create a CalendarEntry for a complex schedule
   calendar_entry = CalendarEntry.objects.create(
       name="Complex Schedule",
       description="A schedule with multiple recurrence patterns",
       timezone=Timezone.objects.get(name="UTC")
   )

   # Event 1: Every Monday and Wednesday
   rule1 = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=["MO", "WE"]
   )

   event1 = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0),
       recurrence_rule=rule1
   )

   # Event 2: First Friday of every month
   rule2 = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.MONTHLY,
       interval=1,
       byweekday=["FR"],
       bysetpos=[1]  # First occurrence
   )

   event2 = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=14, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=15, minute=0, second=0, microsecond=0),
       recurrence_rule=rule2
   )

   calendar_entry.recalculate_occurrences()

Accessing rruleset and rrules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can access the rruleset for a CalendarEntry and individual rrules for each event:

.. code-block:: python

   # Get the rruleset for a CalendarEntry
   calendar_entry = CalendarEntry.objects.get(name="Complex Schedule")
   rruleset = calendar_entry.to_rruleset()

   # Get the next 5 occurrences
   next_occurrences = list(rruleset)[:5]

   # Access individual rrules for each event
   for event in calendar_entry.events.all():
       if event.recurrence_rule:
           rrule = event.recurrence_rule.to_rrule(event.start_time)
           # Use the rrule object as needed

Recalculating Occurrences
~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure the `next_occurrence` and `previous_occurrence` fields are up-to-date, call `recalculate_occurrences()` after making changes:

.. code-block:: python

   calendar_entry.recalculate_occurrences()

You can also recalculate occurrences when saving:

.. code-block:: python

   calendar_entry.save(recalculate=True)

Exporting to iCal Format
~~~~~~~~~~~~~~~~~~~~~~~~

django-recurring supports exporting CalendarEntries to iCal format:

.. code-block:: python

   calendar_entry = CalendarEntry.objects.get(name="Weekly Team Meeting")
   ical_string = calendar_entry.to_ical()

   # You can also specify a custom PRODID
   custom_ical_string = calendar_entry.to_ical(prod_id="-//My Company//My Product//EN")

   # Save the iCal string to a file
   with open('team_meeting.ics', 'w') as f:
       f.write(ical_string)

This will create an iCal file containing all events and their recurrence rules, which can be imported into most calendar applications.
