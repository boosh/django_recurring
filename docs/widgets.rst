=======
Widgets
=======

django-recurring provides custom widgets to enhance the user interface for creating and editing recurrence rules and sets. These widgets are designed to work with the custom forms and provide a more intuitive way to manage complex recurrence patterns.

RecurrenceSetWidget
-------------------

.. py:class:: RecurrenceSetWidget

    A custom widget for the RecurrenceSet model. This widget provides an interface for managing multiple recurrence rules and specific dates within a recurrence set.

    .. py:attribute:: template_name

        Set to "admin/recurring/recurrence_set_widget.html"

    .. py:attribute:: Media

        Defines the required JavaScript and CSS files for the widget.

    .. py:method:: render(self, name, value, attrs=None, renderer=None)

        Renders the widget. It includes the recurrence rules and dates associated with the RecurrenceSet.

RecurrenceRuleWidget
--------------------

.. py:class:: RecurrenceRuleWidget

    A custom widget for the RecurrenceRule model. This widget provides an interface for creating and editing individual recurrence rules.

    .. py:attribute:: template_name

        Set to "admin/recurring/recurrence_rule_widget.html"

    .. py:attribute:: Media

        Defines the required JavaScript and CSS files for the widget.

    .. py:method:: render(self, name, value, attrs=None, renderer=None)

        Renders the widget. It includes all the fields necessary for defining a recurrence rule.

Using the Widgets
-----------------

These widgets are automatically used in the admin interface when you register the RecurrenceSet and RecurrenceRule models with the admin site.

If you want to use these widgets in your own forms outside of the admin, you can do so like this:

.. code-block:: python

    from django import forms
    from recurring.widgets import RecurrenceSetWidget, RecurrenceRuleWidget
    from recurring.models import RecurrenceSet, RecurrenceRule

    class CustomRecurrenceSetForm(forms.ModelForm):
        class Meta:
            model = RecurrenceSet
            fields = ['name', 'description', 'timezone']
            widgets = {
                'recurrence_set': RecurrenceSetWidget(),
            }

    class CustomRecurrenceRuleForm(forms.ModelForm):
        class Meta:
            model = RecurrenceRule
            fields = '__all__'
            widgets = {
                'recurrence_rule': RecurrenceRuleWidget(),
            }

Remember to include the necessary JavaScript and CSS files in your templates when using these widgets outside of the admin interface. You can do this by including the widget's media:

.. code-block:: html

    {{ form.media }}

These widgets provide a user-friendly interface for managing complex recurrence patterns, making it easier for users to create and edit recurring events in your Django application.
