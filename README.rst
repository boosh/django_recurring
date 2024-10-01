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

Create repeating datetimes in Django using dateutil rrulesets with timezone awareness.

* Free software: MIT license
* Documentation: https://django-recurring.readthedocs.io
* Git repo: https://github.com/boosh/django_recurring

Features
--------

* Create complex recurring date patterns using dateutil rrulesets
* Automatically calculate previous and next occurrences for efficient date range queries
* Timezone-aware datetime handling
* Export recurrence sets to iCal format
* Admin interface with custom widget for creating and editing recurrence patterns

Limitations
-----------
This library currently has the following limitations.

* All date ranges require an end date.
    The `count <https://icalendar.org/iCalendar-RFC-5545/3-3-10-recurrence-rule.html>`_ param isn't supported.

PRs welcome.

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

4. Add a RecurrenceSet to your model:

   .. code-block:: python

      from django.db import models
      from recurring.models import RecurrenceSet

      class Event(models.Model):
          name = models.CharField(max_length=200)
          recurrence = models.ForeignKey(RecurrenceSet, on_delete=models.CASCADE)

5. Use the RecurrenceSet in your code:

   .. code-block:: python

      from django.utils import timezone
      from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule

      # Create a RecurrenceSet
      recurrence_set = RecurrenceSet.objects.create(name="Weekly Meeting")

      # Create a RecurrenceRule
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

      # Link the rule to the RecurrenceSet
      RecurrenceSetRule.objects.create(
          recurrence_set=recurrence_set,
          recurrence_rule=rule
      )

      # Recalculate occurrences
      recurrence_set.recalculate_occurrences()

      # Query events within a date range
      events = Event.objects.filter(
          recurrence__next_occurrence__gte=timezone.now(),
          recurrence__previous_occurrence__lte=timezone.now() + timezone.timedelta(days=30)
      )

6. Export to iCal format:

   .. code-block:: python

      ical_string = recurrence_set.to_ical()
      with open('weekly_meeting.ics', 'w') as f:
          f.write(ical_string)

For more detailed usage and examples, see the `documentation <https://django-recurring.readthedocs.io>`_.

Why?
----
`django-recurrence <https://github.com/jazzband/django-recurrence>`_ lacks multiple features (e.g. times, hourly intervals, etc) that don't seem possible to solve. A new library was in order.
