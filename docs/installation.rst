Installation

============
Installation
============

Stable release
--------------

To install django-recurring, run this command in your terminal:

.. code-block:: console

    $ pip install django-recurring

This is the preferred method to install django-recurring, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

Django Configuration
--------------------

After installing django-recurring, you need to add it to your Django project's settings:

1. Add 'recurring' to your INSTALLED_APPS in your Django settings file:

   .. code-block:: python

       INSTALLED_APPS = [
           ...
           'recurring',
           ...
       ]

2. If you want to export to ical, you can optionally configure the `PRODID <https://icalendar.org/iCalendar-RFC-5545/3-7-3-product-identifier.html>`_ value via the following setting:

   .. code-block:: python

       ICAL_PROD_ID="-//My Company//My Product//EN"

3. Run migrations to create the necessary database tables:

   .. code-block:: console

       $ python manage.py migrate recurring

4. Run `collectstatic` for prod releases:

   .. code-block:: console

       $ python manage.py collectstatic

From sources
------------

The sources for django-recurring can be downloaded from the `Github repo`_.

You can clone the public repository:

.. code-block:: console

    $ git clone git://github.com/boosh/django_recurring

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ cd django_recurring
    $ pip install -e .

.. _Github repo: https://github.com/boosh/django_recurring

Compatibility
-------------

django-recurring is tested with:

- Python 3.12.6+
- Django 5.1+
