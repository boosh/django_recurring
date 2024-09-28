=====
Usage
=====

django-recurring provides a set of models, forms, and widgets to help you manage recurring events in your Django project. Here's a basic guide on how to use the main components:

Models
------

The main models you'll be working with are:

1. RecurrenceRule
2. RecurrenceSet
3. RecurrenceSetRule
4. RecurrenceDate

Here's a basic example of creating a RecurrenceSet:

.. code-block:: python

    from recurring.models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, Timezone

    # Create a timezone
    timezone, _ = Timezone.objects.get_or_create(name="UTC")

    # Create a RecurrenceSet
    recurrence_set = RecurrenceSet.objects.create(
        name="Weekly Meeting",
        description="Team sync-up every Monday",
        timezone=timezone
    )

    # Create a RecurrenceRule
    rule = RecurrenceRule.objects.create(
        frequency=RecurrenceRule.Frequency.WEEKLY,
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

Forms
-----

django-recurring provides custom forms for RecurrenceRule and RecurrenceSet. You can use these in your views:

.. code-block:: python

    from django.shortcuts import render, redirect
    from recurring.forms import RecurrenceSetForm

    def create_recurrence_set(request):
        if request.method == 'POST':
            form = RecurrenceSetForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('recurrence_set_list')
        else:
            form = RecurrenceSetForm()
        return render(request, 'create_recurrence_set.html', {'form': form})

Widgets
-------

The RecurrenceSetWidget and RecurrenceRuleWidget are automatically used in the admin interface. If you want to use them in your own forms, you can do so like this:

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

For more detailed usage examples, please refer to the Examples section.

Using with Custom Models
------------------------

Here's an example of how to use django-recurring with your own models to add recurrence to an Event model:

.. code-block:: python

    from django.db import models
    from recurring.models import RecurrenceSet

    class Event(models.Model):
        title = models.CharField(max_length=200)
        description = models.TextField(blank=True)
        start_time = models.TimeField()
        duration = models.DurationField()
        recurrence_set = models.ForeignKey(RecurrenceSet, on_delete=models.SET_NULL, null=True, blank=True)

        def __str__(self):
            return self.title

        def get_occurrences(self, start_date, end_date):
            if not self.recurrence_set:
                return []

            rruleset = self.recurrence_set.to_rruleset()
            occurrences = []

            for dt in rruleset.between(start_date, end_date):
                occurrence_start = dt.replace(hour=self.start_time.hour, minute=self.start_time.minute)
                occurrence_end = occurrence_start + self.duration
                occurrences.append((occurrence_start, occurrence_end))

            return occurrences

In this example:

1. We define an `Event` model with a `ForeignKey` to `RecurrenceSet`.
2. The `get_occurrences` method uses the `RecurrenceSet` to generate all occurrences of the event between two dates.

You can use this model in your views like this:

.. code-block:: python

    from django.shortcuts import render
    from .models import Event
    from datetime import datetime, timedelta

    def event_list(request):
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30)  # Show events for the next 30 days

        events = Event.objects.all()
        occurrences = []

        for event in events:
            event_occurrences = event.get_occurrences(start_date, end_date)
            for start, end in event_occurrences:
                occurrences.append({
                    'title': event.title,
                    'start': start,
                    'end': end,
                })

        return render(request, 'event_list.html', {'occurrences': occurrences})

This view fetches all events and their occurrences for the next 30 days, which you can then display in your template.
