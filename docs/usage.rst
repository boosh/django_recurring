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
