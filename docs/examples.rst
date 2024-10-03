========
Examples
========

This page provides various examples of how to use django-recurring in your Django projects.

.. note::

    This documentation was generated with AI. Code examples may not be 100% accurate. For tested, working code, see the source for the `save()` method in `forms.py <https://django-recurring.readthedocs.io/en/latest/_modules/recurring/forms.html#CalendarEntryForm.save>`_

Creating a CalendarEntry with Multiple Events
---------------------------------------------

.. code-block:: python

   from django.utils import timezone
   from recurring.models import CalendarEntry, Event, RecurrenceRule, Timezone, MONDAY, FRIDAY

   # Create a CalendarEntry for team meetings
   calendar_entry = CalendarEntry.objects.create(
       name="Team Meetings",
       description="Regular team sync-ups",
       timezone=Timezone.objects.get(name="UTC")
   )

   # Create a weekly meeting event
   weekly_rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=[MONDAY]
   )

   weekly_event = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0),
       recurrence_rule=weekly_rule
   )

   # Create a monthly meeting event
   monthly_rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.MONTHLY,
       interval=1,
       bysetpos=[1],  # First occurrence
       byweekday=[FRIDAY]
   )

   monthly_event = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=14, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=15, minute=0, second=0, microsecond=0),
       recurrence_rule=monthly_rule
   )

Complex Recurrence Pattern
--------------------------

.. code-block:: python

   from recurring.models import CalendarEntry, Event, RecurrenceRule, Timezone, MONDAY, WEDNESDAY, FRIDAY

   # Create a CalendarEntry for a complex schedule
   calendar_entry = CalendarEntry.objects.create(
       name="Complex Schedule",
       description="A schedule with multiple recurrence patterns",
       timezone=Timezone.objects.get(name="UTC")
   )

   # Create an event that occurs every Monday, Wednesday, and the first Friday of each month
   complex_rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.WEEKLY,
       interval=1,
       byweekday=[MONDAY, WEDNESDAY],  # Every Monday and Wednesday
   )

   complex_event = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0),
       recurrence_rule=complex_rule
   )

   # Add a monthly recurrence for the first Friday
   monthly_friday_rule = RecurrenceRule.objects.create(
       frequency=RecurrenceRule.Frequency.MONTHLY,
       interval=1,
       bysetpos=[1],  # First occurrence
       byweekday=[FRIDAY]
   )

   monthly_friday_event = Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=12, minute=0, second=0, microsecond=0),
       recurrence_rule=monthly_friday_rule
   )



Accessing rruleset and rrules
-----------------------------

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

Using CalendarEntry in Your Own Model
-------------------------------------

.. code-block:: python

   from django.db import models
   from recurring.models import CalendarEntry

   class Meeting(models.Model):
       title = models.CharField(max_length=200)
       calendar_entry = models.ForeignKey(CalendarEntry, on_delete=models.CASCADE)

   # Create a meeting with a calendar entry
   calendar_entry = CalendarEntry.objects.create(
       name="Board Meetings",
       description="Regular board meetings",
       timezone=Timezone.objects.get(name="UTC")
   )

   # Add an event to the calendar entry
   Event.objects.create(
       calendar_entry=calendar_entry,
       start_time=timezone.now().replace(hour=13, minute=0, second=0, microsecond=0),
       end_time=timezone.now().replace(hour=14, minute=0, second=0, microsecond=0),
       recurrence_rule=RecurrenceRule.objects.create(
           frequency=RecurrenceRule.Frequency.MONTHLY,
           interval=1,
           byweekday=["TU"],  # Every Tuesday
           bysetpos=[2]  # Second occurrence
       )
   )

   meeting = Meeting.objects.create(title="Monthly Board Meeting", calendar_entry=calendar_entry)

   # Query meetings within a date range
   upcoming_meetings = Meeting.objects.filter(
       calendar_entry__next_occurrence__gte=timezone.now(),
       calendar_entry__next_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
   )

.. important::

    See notes on :ref:`recalculating occurrences <recalculating-occurrences>`

Exporting to iCal Format
------------------------

django-recurring supports exporting CalendarEntries to iCal format:

.. code-block:: python

   calendar_entry = CalendarEntry.objects.get(name="Board Meetings")
   ical_string = calendar_entry.to_ical()

   # Optionally, you can specify a custom PRODID
   custom_ical_string = calendar_entry.to_ical(prod_id="-//My Company//My Product//EN")

   # You can then save this to a file or send it as a response
   with open('board_meetings.ics', 'w') as f:
       f.write(ical_string)

The resulting iCal file will contain all the events and their recurrence rules, which can be imported into most calendar applications.
