======
Models
======

django-recurring provides several models to handle recurring events and schedules. Here's a detailed explanation of each model:

Timezone
--------

.. py:class:: Timezone

    Represents a timezone.

    .. py:attribute:: name

        A CharField that stores the name of the timezone.

RecurrenceRule
--------------

.. py:class:: RecurrenceRule

    Represents a single recurrence rule.

    .. py:attribute:: frequency

        An IntegerField that stores the frequency of the recurrence (e.g., YEARLY, MONTHLY, WEEKLY, etc.).

    .. py:attribute:: interval

        An IntegerField that stores the interval between each frequency iteration.

    .. py:attribute:: wkst

        An IntegerField that stores the week start day.

    .. py:attribute:: count

        An IntegerField that stores how many occurrences will be generated.

    .. py:attribute:: bysetpos

        A JSONField that stores the BYSETPOS rule.

    .. py:attribute:: bymonth

        A JSONField that stores the BYMONTH rule.

    .. py:attribute:: bymonthday

        A JSONField that stores the BYMONTHDAY rule.

    .. py:attribute:: byyearday

        A JSONField that stores the BYYEARDAY rule.

    .. py:attribute:: byweekno

        A JSONField that stores the BYWEEKNO rule.

    .. py:attribute:: byweekday

        A JSONField that stores the BYDAY rule.

    .. py:attribute:: byhour

        A JSONField that stores the BYHOUR rule.

    .. py:attribute:: byminute

        A JSONField that stores the BYMINUTE rule.

    .. py:attribute:: bysecond

        A JSONField that stores the BYSECOND rule.

    .. py:attribute:: timezone

        A ForeignKey to the Timezone model.

    .. py:method:: to_rrule(start_date, end_date)

        Converts the RecurrenceRule to a dateutil.rrule.rrule object.

    .. py:method:: to_dict()

        Converts the RecurrenceRule to a dictionary representation.

RecurrenceRuleDateRange
-----------------------

.. py:class:: RecurrenceRuleDateRange

    Represents a date range for a RecurrenceRule.

    .. py:attribute:: recurrence_rule

        A ForeignKey to the RecurrenceRule model.

    .. py:attribute:: start_date

        A DateTimeField that stores the start date of the date range.

    .. py:attribute:: end_date

        A DateTimeField that stores the end date of the date range.

    .. py:attribute:: is_exclusion

        A BooleanField that indicates whether this date range is an exclusion.

RecurrenceSet
-------------

.. py:class:: RecurrenceSet

    Represents a set of recurrence rules.

    .. py:attribute:: name

        A CharField that stores the name of the recurrence set.

    .. py:attribute:: description

        A TextField that stores a description of the recurrence set.

    .. py:attribute:: timezone

        A ForeignKey to the Timezone model.

    .. py:attribute:: next_occurrence

        A DateTimeField that stores the next occurrence of this recurrence set.

    .. py:attribute:: previous_occurrence

        A DateTimeField that stores the previous occurrence of this recurrence set.

    .. py:method:: to_rruleset()

        Converts the RecurrenceSet to a dateutil.rrule.rruleset object.

    .. py:method:: to_dict()

        Converts the RecurrenceSet to a dictionary representation.

    .. py:method:: from_dict(data)

        Creates a RecurrenceSet from a dictionary representation.

    .. py:method:: recalculate_occurrences()

        Recalculates the next and previous occurrences for this RecurrenceSet.

    .. py:method:: to_ical(prod_id=None)

        Converts the RecurrenceSet to an iCal string representation.

RecurrenceSetRule
-----------------

.. py:class:: RecurrenceSetRule

    Represents the relationship between a RecurrenceSet and a RecurrenceRule.

    .. py:attribute:: recurrence_set

        A ForeignKey to the RecurrenceSet model.

    .. py:attribute:: recurrence_rule

        A OneToOneField to the RecurrenceRule model.

    .. py:attribute:: is_exclusion

        A BooleanField that indicates whether this rule is an exclusion rule.

These models work together to create complex recurring schedules. The RecurrenceSet is the main model that you'll typically associate with your application's models. It contains one or more RecurrenceRules (via RecurrenceSetRule), each of which can have one or more RecurrenceRuleDateRanges.
