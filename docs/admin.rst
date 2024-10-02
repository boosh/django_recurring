=====
Admin
=====

Widget
------

django-recurring ships with a javascript widget for the Django admin interface to create complex intervals easily. Recurrence rules can have multiple exclusions:

.. image:: widget-advanced.png
   :alt: Widget advanced image
   :align: center

It supports multiple events, each with recurrence patterns:

.. image:: widget-simple.png
   :alt: Widget simple image
   :align: center

Together, this allows creating complex recurrences like:

    Every Monday in Jan & Feb, every Tuesday in Mar and Apr, except the 3rd weeks of Feb and Apr.

iCal
------
The iCal string for the calendar entry is also displayed in the admin and can be downloaded as an ical (.ics) file:

.. image:: widget-ical.png
   :alt: Widget ical image
   :align: center
