========
Examples
========

This page provides various examples of how to use django-recurring in your Django projects.

Creating a Simple Weekly Recurrence
-----------------------------------

Here's an example of creating a simple weekly recurrence for a team meeting:

.. code-block:: python

    from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, Timezone
    from dateutil.rrule import WEEKLY, MO

    # Create or get the timezone
    timezone, _ = Timezone.objects.get_or_create(name="UTC")

    # Create the RecurrenceSet
    recurrence_set = RecurrenceSet.objects.create(
        name="Weekly Team Meeting",
        description="Our team's weekly sync-up",
        timezone=timezone
    )

    # Create the RecurrenceRule
    rule = RecurrenceRule.objects.create(
        frequency=WEEKLY,
        interval=1,
        byweekday="[0]",  # Monday
        timezone=timezone
    )

    # Associate the rule with the RecurrenceSet
    RecurrenceSetRule.objects.create(
        recurrence_set=recurrence_set,
        recurrence_rule=rule,
        is_exclusion=False
    )

Creating a Monthly Recurrence with Exceptions
---------------------------------------------

Here's an example of creating a monthly recurrence for a board meeting, with some exceptions:

.. code-block:: python

    from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, RecurrenceDate, Timezone
    from dateutil.rrule import MONTHLY
    from django.utils import timezone

    # Create or get the timezone
    timezone_obj, _ = Timezone.objects.get_or_create(name="UTC")

    # Create the RecurrenceSet
    recurrence_set = RecurrenceSet.objects.create(
        name="Monthly Board Meeting",
        description="Board meeting on the first Monday of each month",
        timezone=timezone_obj
    )

    # Create the RecurrenceRule
    rule = RecurrenceRule.objects.create(
        frequency=MONTHLY,
        interval=1,
        byweekday="[0]",  # Monday
        bysetpos="[1]",   # First occurrence
        timezone=timezone_obj
    )

    # Associate the rule with the RecurrenceSet
    RecurrenceSetRule.objects.create(
        recurrence_set=recurrence_set,
        recurrence_rule=rule,
        is_exclusion=False
    )

    # Add an exception date (e.g., skip the meeting in July)
    exception_date = timezone.now().replace(year=2023, month=7, day=3, hour=9, minute=0, second=0, microsecond=0)
    RecurrenceDate.objects.create(
        recurrence_set=recurrence_set,
        date=exception_date,
        is_exclusion=True
    )

Using the RecurrenceSetWidget in a Custom Form
----------------------------------------------

Here's an example of how to use the RecurrenceSetWidget in a custom form:

.. code-block:: python

    from django import forms
    from recurring.widgets import RecurrenceSetWidget
    from recurring.models import RecurrenceSet

    class CustomRecurrenceSetForm(forms.ModelForm):
        class Meta:
            model = RecurrenceSet
            fields = ['name', 'description', 'timezone']
            widgets = {
                'recurrence_set': RecurrenceSetWidget(),
            }

    # In your view
    from django.shortcuts import render, redirect

    def create_recurrence_set(request):
        if request.method == 'POST':
            form = CustomRecurrenceSetForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('recurrence_set_list')
        else:
            form = CustomRecurrenceSetForm()
        return render(request, 'create_recurrence_set.html', {'form': form})

Querying for Upcoming Occurrences
---------------------------------

Here's an example of how to query for upcoming occurrences of a RecurrenceSet:

.. code-block:: python

    from recurring.models import RecurrenceSet
    from django.utils import timezone
    import pytz

    def get_upcoming_occurrences(recurrence_set, limit=5):
        rruleset = recurrence_set.to_rruleset()
        now = timezone.now()
        tz = pytz.timezone(recurrence_set.timezone.name)

        occurrences = list(rruleset.after(now, inc=False, count=limit))
        return [occurrence.astimezone(tz) for occurrence in occurrences]

    # Usage
    recurrence_set = RecurrenceSet.objects.get(name="Weekly Team Meeting")
    upcoming = get_upcoming_occurrences(recurrence_set)
    for occurrence in upcoming:
        print(occurrence)

These examples should give you a good starting point for working with django-recurring. Remember to adjust the timezone, dates, and other parameters according to your specific use case.
