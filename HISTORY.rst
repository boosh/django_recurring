=======
History
=======
0.3.4 (2024-10-06)
------------------
* Full timezone support
    * Display local datetimes in the admin widget
    * Correctly convert to UTC when saving data

0.3.3 (2024-10-03)
------------------
* Add an option to repeat events forever
* Calculate prev/next occurrences more efficiently
* Also calculate the first/last occurrences within a bounded range
* Make the calendar entry name mandatory
* Support hourly and minutely repeating events

0.3.0 (2024-10-02)
------------------
* Breaking change: Total refactoring of models to better align with ical/dateutil rrules.

0.2.0 (2024-10-01)
------------------
* Allow downloading ical strings from the admin

0.1.0 (2024-09-28)
------------------

* First release on PyPI.
