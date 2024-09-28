======
Models
======

django-recurring provides several models to represent recurring events and their rules. Here's a detailed explanation of each model:

Timezone
--------

.. py:class:: Timezone

    Represents a timezone.

    .. py:attribute:: name

        A CharField that stores the name of the timezone.

RecurrenceRule
--------------

.. py:class:: RecurrenceRule

    Represents a recurrence rule, which defines how an event repeats.

    .. py:attribute:: frequency

        An IntegerField that stores the frequency of the recurrence (e.g., DAILY, WEEKLY, MONTHLY, YEARLY).

    .. py:attribute:: interval

        An IntegerField that represents the interval between each frequency iteration.

    .. py:attribute:: wkst

        An IntegerField that represents the week start day.

    .. py:attribute:: count

        An IntegerField that specifies how many occurrences will be generated.

    .. py:attribute:: until

        A DateTimeField that specifies a date to repeat until.

    .. py:attribute:: bysetpos

        A CharField that stores the BYSETPOS rule.

    .. py:attribute:: bymonth

        A CharField that stores the BYMONTH rule.

    .. py:attribute:: bymonthday

        A CharField that stores the BYMONTHDAY rule.

    .. py:attribute:: byyearday

        A CharField that stores the BYYEARDAY rule.

    .. py:attribute:: byweekno

        A CharField that stores the BYWEEKNO rule.

    .. py:attribute:: byweekday

        A CharField that stores the BYDAY rule.

    .. py:attribute:: byhour

        A CharField that stores the BYHOUR rule.

    .. py:attribute:: byminute

        A CharField that stores the BYMINUTE rule.

    .. py:attribute:: bysecond

        A CharField that stores the BYSECOND rule.

    .. py:attribute:: timezone

        A ForeignKey to the Timezone model.

    .. py:method:: to_rrule()

        Converts the RecurrenceRule to a dateutil.rrule.rrule object.

    .. py:method:: to_ical()

        Converts the RecurrenceRule to an iCalendar RRULE string.

    .. py:classmethod:: from_ical(cls, ical_string, timezone="UTC")

        Creates a RecurrenceRule object from an iCalendar RRULE string.

RecurrenceSet
-------------

.. py:class:: RecurrenceSet

    Represents a set of recurrence rules and dates.

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

    .. py:method:: to_ical()

        Converts the RecurrenceSet to an iCalendar string.

    .. py:classmethod:: from_ical(cls, ical_string)

        Creates a RecurrenceSet object from an iCalendar string.

    .. py:method:: recalculate_occurrences()

        Recalculates the next and previous occurrences of the recurrence set.

RecurrenceSetRule
-----------------

.. py:class:: RecurrenceSetRule

    Represents the association between a RecurrenceSet and a RecurrenceRule.

    .. py:attribute:: recurrence_set

        A ForeignKey to the RecurrenceSet model.

    .. py:attribute:: recurrence_rule

        A ForeignKey to the RecurrenceRule model.

    .. py:attribute:: is_exclusion

        A BooleanField that indicates whether this rule is an exclusion rule.

RecurrenceDate
--------------

.. py:class:: RecurrenceDate

    Represents a specific date in a RecurrenceSet, which can be either an inclusion or an exclusion.

    .. py:attribute:: recurrence_set

        A ForeignKey to the RecurrenceSet model.

    .. py:attribute:: date

        A DateTimeField that stores the specific date.

    .. py:attribute:: is_exclusion

        A BooleanField that indicates whether this date is an exclusion date.

These models work together to create flexible and powerful recurrence patterns for your events. The RecurrenceSet is the main model that you'll work with, which can contain multiple RecurrenceSetRules (each associated with a RecurrenceRule) and RecurrenceDates.
