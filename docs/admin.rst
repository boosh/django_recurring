=====
Admin
=====

django-recurring provides custom admin classes to enhance the management of RecurrenceRules and RecurrenceSets in the Django admin interface. These admin classes use the custom forms and widgets to provide a user-friendly interface for creating and editing complex recurrence patterns.

RecurrenceRuleAdmin
-------------------

.. py:class:: RecurrenceRuleAdmin

    A custom admin class for the RecurrenceRule model.

    .. py:attribute:: form

        Set to RecurrenceRuleForm to use the custom form with the RecurrenceRuleWidget.

RecurrenceSetAdmin
------------------

.. py:class:: RecurrenceSetAdmin

    A custom admin class for the RecurrenceSet model.

    .. py:attribute:: form

        Set to RecurrenceSetForm to use the custom form with the RecurrenceSetWidget.

    .. py:attribute:: list_display

        Displays 'name', 'timezone', 'next_occurrence', and 'previous_occurrence' in the admin list view.

    .. py:attribute:: search_fields

        Allows searching by 'name'.

    .. py:attribute:: list_filter

        Allows filtering by 'timezone'.

    .. py:method:: get_form(self, request, obj=None, **kwargs)

        Overrides the default get_form method to add formsets for RecurrenceSetRules and RecurrenceDates.

    .. py:method:: save_model(self, request, obj, form, change)

        Overrides the default save_model method to save the formsets along with the RecurrenceSet.

Registering Models with Admin
-----------------------------

The models are registered with the admin site in the admin.py file:

.. code-block:: python

    from django.contrib import admin
    from .models import Timezone, RecurrenceRule, RecurrenceSet, RecurrenceSetRule, RecurrenceDate
    from .admin import RecurrenceRuleAdmin, RecurrenceSetAdmin

    admin.site.register(Timezone)
    admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
    admin.site.register(RecurrenceSet, RecurrenceSetAdmin)
    admin.site.register(RecurrenceSetRule)
    admin.site.register(RecurrenceDate)

This registration makes all the models available in the Django admin interface, with RecurrenceRule and RecurrenceSet using their custom admin classes.

Using the Admin Interface
-------------------------

Once the models are registered, you can access them in the Django admin interface. Here's how you can use it:

1. Navigate to the Django admin interface (usually at /admin/).
2. You'll see sections for Timezone, RecurrenceRule, RecurrenceSet, RecurrenceSetRule, and RecurrenceDate.
3. To create a new RecurrenceSet:
   - Click on '+ Add' next to RecurrenceSet.
   - Fill in the name, description, and select a timezone.
   - Use the RecurrenceSetWidget to add recurrence rules and specific dates.
   - Click 'Save' to create the RecurrenceSet.
4. To edit an existing RecurrenceSet:
   - Click on the RecurrenceSet name in the list view.
   - Modify the fields as needed.
   - Use the RecurrenceSetWidget to add, edit, or remove recurrence rules and specific dates.
   - Click 'Save' to update the RecurrenceSet.

The custom admin interface provides an intuitive way to manage complex recurrence patterns directly in the Django admin, making it easier to create and maintain recurring events in your application.
