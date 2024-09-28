=====
Forms
=====

django-recurring provides custom forms to handle the creation and editing of RecurrenceRules and RecurrenceSets. These forms are designed to work with the custom widgets and provide a user-friendly interface for managing complex recurrence patterns.

RecurrenceRuleForm
------------------

.. py:class:: RecurrenceRuleForm

    A ModelForm for the RecurrenceRule model.

    This form uses the RecurrenceRuleWidget for a more intuitive interface for creating and editing recurrence rules.

    .. py:attribute:: Meta

        .. py:attribute:: model

            Set to RecurrenceRule

        .. py:attribute:: fields

            Set to "__all__" to include all fields from the RecurrenceRule model

        .. py:attribute:: widgets

            Uses the RecurrenceRuleWidget for the 'recurrence_rule' field

RecurrenceSetForm
-----------------

.. py:class:: RecurrenceSetForm

    A ModelForm for the RecurrenceSet model.

    This form includes formsets for RecurrenceSetRules and RecurrenceDates, allowing users to add multiple rules and specific dates to a RecurrenceSet.

    .. py:attribute:: Meta

        .. py:attribute:: model

            Set to RecurrenceSet

        .. py:attribute:: fields

            Includes 'name', 'description', and 'timezone'

        .. py:attribute:: widgets

            Uses the RecurrenceSetWidget for the 'recurrence_set' field

    .. py:method:: __init__(self, *args, **kwargs)

        Initializes the form and creates formsets for RecurrenceSetRules and RecurrenceDates.

    .. py:method:: is_valid(self)

        Checks if the form and all its formsets are valid.

    .. py:method:: save(self, commit=True)

        Saves the form and all its formsets.

RecurrenceSetRuleForm
---------------------

.. py:class:: RecurrenceSetRuleForm

    A ModelForm for the RecurrenceSetRule model.

    .. py:attribute:: Meta

        .. py:attribute:: model

            Set to RecurrenceSetRule

        .. py:attribute:: fields

            Includes 'recurrence_rule' and 'is_exclusion'

RecurrenceDateForm
------------------

.. py:class:: RecurrenceDateForm

    A ModelForm for the RecurrenceDate model.

    .. py:attribute:: Meta

        .. py:attribute:: model

            Set to RecurrenceDate

        .. py:attribute:: fields

            Includes 'date' and 'is_exclusion'

Using these forms in your views
-------------------------------

Here's an example of how to use the RecurrenceSetForm in a view:

.. code-block:: python

    from django.shortcuts import render, redirect
    from recurring.forms import RecurrenceSetForm

    def create_recurrence_set(request):
        if request.method == 'POST':
            form = RecurrenceSetForm(request.POST)
            if form.is_valid():
                recurrence_set = form.save()
                return redirect('recurrence_set_detail', pk=recurrence_set.pk)
        else:
            form = RecurrenceSetForm()
        return render(request, 'create_recurrence_set.html', {'form': form})

This view will handle both GET and POST requests, creating a new RecurrenceSet when the form is submitted successfully.

Remember to create the corresponding template (`create_recurrence_set.html` in this example) that renders the form and handles form submission.
