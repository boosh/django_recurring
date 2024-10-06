=====
Admin
=====

Widget
------

django-recurring ships with a javascript widget for the Django admin interface to create complex intervals easily. Recurrence rules can have multiple exclusions:

.. image:: images/widget-advanced.png
   :alt: Widget advanced image
   :align: center

It supports multiple events, each with recurrence patterns:

.. image:: images/widget-simple.png
   :alt: Widget simple image
   :align: center

Together, this allows creating complex recurrences like:

    Every Monday in Jan & Feb, every Tuesday in Mar and Apr, except the 3rd weeks of Feb and Apr.

Timezones
---------
Event times can be associated with any timezone. Just create/select them in the admin:

.. image:: images/admin-timezones.png
   :alt: Timezones image
   :align: center

Enter all times in the main widget in your selected timezone's local time.

iCal
------
The iCal string for the calendar entry is also displayed in the admin and can be downloaded as an ical (.ics) file:

.. image:: images/widget-ical.png
   :alt: Widget ical image
   :align: center

List view
---------
The admin also includes the precomputed :ref:`occurrence fields <recalculating-occurrences>` in the list view by default:

.. image:: images/admin-list-view.png
   :alt: Admin list view image
   :align: center
