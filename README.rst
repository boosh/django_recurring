================
django-recurring
================

.. image:: https://img.shields.io/pypi/v/django_recurring.svg
        :target: https://pypi.python.org/pypi/django_recurring

.. image:: https://img.shields.io/travis/boosh/django_recurring.svg
        :target: https://travis-ci.com/boosh/django_recurring

.. image:: https://readthedocs.org/projects/django-recurring/badge/?version=latest
        :target: https://django-recurring.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

Create ical-compatible calendar events in django. This library is good if you need:

* iCal-compatible calendar entries with multiple events and (optionally) complex recurrence rules and multiple exclusions
* Calendar entries you can export to iCal format (.ics files)
* To add complex recurrence rules (i.e. repeating events) to your models and interact with them as dateutil rrulesets

Free software: MIT license

Links
-----
* Documentation: https://django-recurring.readthedocs.io
* Git repo: https://github.com/boosh/django_recurring

Status
--------

Initial release. There are likely to be bugs.

The 0.x series is for development only and should not be used in live projects. Semver is ignored on the 0.x branch.

Features
--------

* Create calendar entries/schedules with multiple events, recurrence rules and exclusions
    * E.g. Every Monday in Jan & Feb, every Tuesday in Mar and Apr, except the 3rd weeks of Feb and Apr.
* Access recurrences using dateutil rrulesets
* Automatically calculate previous and next occurrences for efficient date range queries
* Timezone-aware datetime handling
* Export to iCal format (.ics files)
* `Admin widget <https://django-recurring.readthedocs.io/en/latest/admin.html>`_ for creating and editing recurrence patterns

Quick Start
-----------

1. Install django-recurring:

   .. code-block:: bash

      pip install django-recurring

2. Add 'recurring' to your INSTALLED_APPS:

   .. code-block:: python

      INSTALLED_APPS = [
          ...
          'recurring',
      ]

3. Run migrations:

   .. code-block:: bash

      python manage.py migrate recurring

4. Add CalendarEntry to your model:

   For a calendar entry with multiple events:

   .. code-block:: python

      from django.db import models
      from recurring.models import CalendarEntry

      class Meeting(models.Model):
          name = models.CharField(max_length=200)
          calendar = models.ForeignKey(CalendarEntry, on_delete=models.CASCADE)

5. Use CalendarEntry in your code:

   .. code-block:: python

      from django.utils import timezone
      from recurring.models import CalendarEntry, Event, RecurrenceRule, Timezone, MONDAY

      # Create a CalendarEntry with multiple events
      calendar = CalendarEntry.objects.create(
          name="Team Meetings",
          timezone=Timezone.objects.get(name="UTC")
      )

      weekly_rule = RecurrenceRule.objects.create(
          frequency=RecurrenceRule.Frequency.WEEKLY,
          interval=1,
          byweekday=[MONDAY]
      )

      Event.objects.create(
          calendar_entry=calendar,
          start_time=timezone.now(),
          end_time=timezone.now() + timezone.timedelta(hours=1),
          recurrence_rule=weekly_rule
      )

      # Create a single recurring event
      monthly_rule = RecurrenceRule.objects.create(
          frequency=RecurrenceRule.Frequency.MONTHLY,
          interval=1,
          bysetpos=[1],
          byweekday=[MONDAY]
      )

      task = Event.objects.create(
          start_time=timezone.now(),
          end_time=timezone.now() + timezone.timedelta(hours=2),
          recurrence_rule=monthly_rule
      )

      # automatically recalculate occurrences now there are some
      # events and recurrence rules
      calendar.save()

      # Query upcoming meetings
      upcoming_meetings = Meeting.objects.filter(
          calendar__next_occurrence__gte=timezone.now(),
          calendar__next_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
      )

      # Query upcoming tasks
      upcoming_tasks = Task.objects.filter(
          schedule__start_time__gte=timezone.now(),
          schedule__start_time__lte=timezone.now() + timezone.timedelta(days=30)
      )

6. Export to iCal format:

   .. code-block:: python

      ical_string = calendar.to_ical()
      with open('team_meetings.ics', 'w') as f:
          f.write(ical_string)

For more detailed usage and examples, see the `documentation <https://django-recurring.readthedocs.io>`_.

Why?
----
`django-recurrence <https://github.com/jazzband/django-recurrence>`_ lacks multiple features (e.g. times, hourly intervals, etc) that don't seem possible to solve. A new library was in order.
