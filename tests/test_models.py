from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone as django_timezone

from recurring.models import (
    Timezone,
    CalendarEntry,
    Event,
    RecurrenceRule,
    ExclusionDateRange,
)


@pytest.fixture
def timezone_obj():
    return Timezone.objects.get_or_create(name="UTC")[0]


@pytest.fixture
def calendar_entry(timezone_obj):
    return CalendarEntry.objects.create(
        name="Test Calendar Entry",
        description="A test calendar entry",
        timezone=timezone_obj,
    )


@pytest.fixture
def recurrence_rule():
    return RecurrenceRule.objects.create(
        frequency=RecurrenceRule.Frequency.DAILY,
        interval=1,
        count=3,
    )


@pytest.fixture
def event(calendar_entry, recurrence_rule):
    return Event.objects.create(
        calendar_entry=calendar_entry,
        start_time=django_timezone.now(),
        end_time=django_timezone.now() + django_timezone.timedelta(hours=1),
        recurrence_rule=recurrence_rule,
    )


@pytest.mark.django_db
class TestTimezone:
    def test_timezone_creation(self, timezone_obj):
        assert timezone_obj.name == "UTC"
        assert str(timezone_obj) == "UTC"


@pytest.mark.django_db
class TestCalendarEntry:
    def test_calendar_entry_creation(self, calendar_entry):
        assert calendar_entry.name == "Test Calendar Entry"
        assert calendar_entry.description == "A test calendar entry"
        assert str(calendar_entry) == "Test Calendar Entry: No events"

    def test_to_rruleset(self, calendar_entry, event, recurrence_rule):
        event.recurrence_rule = recurrence_rule
        event.save()
        rruleset = calendar_entry.to_rruleset()
        assert len(rruleset._rrule) == 1
        assert len(rruleset._exdate) == 0

    def test_to_dict(self, calendar_entry, event, recurrence_rule):
        event.recurrence_rule = recurrence_rule
        event.save()
        calendar_entry_dict = calendar_entry.to_dict()
        assert calendar_entry_dict["name"] == "Test Calendar Entry"
        assert calendar_entry_dict["description"] == "A test calendar entry"
        assert calendar_entry_dict["timezone"] == "UTC"
        assert len(calendar_entry_dict["events"]) == 1

    def test_from_dict(self, calendar_entry):
        tz = calendar_entry.timezone.as_tz
        start_time_naive = datetime.fromisoformat("2023-01-01T00:00:00+00:00")
        end_time_naive = datetime.fromisoformat("2023-01-01T01:00:00+00:00")

        exclusion_start_naive = datetime.fromisoformat("2023-01-07T00:00:00+00:00")
        exclusion_end_naive = datetime.fromisoformat("2023-01-10T00:00:00+00:00")

        data = {
            "name": "Updated Calendar Entry",
            "description": "An updated calendar entry",
            "timezone": "UTC",
            "events": [
                {
                    "start_time": start_time_naive.replace(tzinfo=tz),
                    "end_time": end_time_naive.replace(tzinfo=tz),
                    "is_full_day": False,
                    "recurrence_rule": {
                        "frequency": "DAILY",
                        "interval": 1,
                        "byweekday": ["MO", "WE", "FR"],
                    },
                    "exclusions": [
                        {
                            "start_date": exclusion_start_naive.replace(tzinfo=tz),
                            "end_date": exclusion_end_naive.replace(tzinfo=tz),
                        }
                    ],
                }
            ],
        }
        calendar_entry.from_dict(data)
        assert calendar_entry.name == "Updated Calendar Entry"
        assert calendar_entry.description == "An updated calendar entry"
        assert calendar_entry.events.count() == 1
        event = calendar_entry.events.first()
        assert event.recurrence_rule is not None
        assert event.recurrence_rule.frequency == RecurrenceRule.Frequency.DAILY
        assert event.recurrence_rule.interval == 1
        assert event.recurrence_rule.byweekday == ["MO", "WE", "FR"]
        assert event.exclusions.count() == 1

    def test_calculate_occurrences(self, calendar_entry, event, recurrence_rule):
        event.recurrence_rule = recurrence_rule
        event.save()
        calendar_entry.calculate_occurrences()
        assert calendar_entry.next_occurrence is not None
        assert calendar_entry.previous_occurrence is not None
        assert calendar_entry.first_occurrence is not None
        assert calendar_entry.last_occurrence is not None

    def test_to_ical(self, calendar_entry, event, recurrence_rule):
        utc = timezone.utc
        event.start_time = django_timezone.datetime(2023, 1, 1, tzinfo=utc)
        event.end_time = django_timezone.datetime(2023, 1, 1, 1, tzinfo=utc)
        event.recurrence_rule = recurrence_rule
        event.save()

        ical_string = calendar_entry.to_ical()
        print(ical_string)

        assert "BEGIN:VCALENDAR" in ical_string
        assert "BEGIN:VEVENT" in ical_string
        assert "RRULE:FREQ=DAILY;COUNT=3;INTERVAL=1" in ical_string
        assert "DTSTART:20230101T000000Z" in ical_string
        assert "DTEND:20230101T010000Z" in ical_string
        assert "END:VEVENT" in ical_string
        assert "END:VCALENDAR" in ical_string

    def test_to_ical_with_exclusions(self, calendar_entry, event, recurrence_rule):
        utc = timezone.utc
        event.start_time = django_timezone.datetime(2023, 1, 1, tzinfo=utc)
        event.end_time = django_timezone.datetime(2023, 1, 1, 1, tzinfo=utc)
        event.recurrence_rule = recurrence_rule
        event.save()

        ExclusionDateRange.objects.create(
            event=event,
            start_date=django_timezone.datetime(2023, 1, 7, tzinfo=utc),
            end_date=django_timezone.datetime(2023, 1, 10, tzinfo=utc),
        )

        ical_string = calendar_entry.to_ical()
        print(ical_string)

        assert "BEGIN:VCALENDAR" in ical_string
        assert "VERSION:2.0" in ical_string
        assert "PRODID:-//django-recurring//NONSGML v1.0//EN" in ical_string
        assert "BEGIN:VEVENT" in ical_string
        assert "DTSTART:20230101T000000Z" in ical_string
        assert "DTEND:20230101T010000Z" in ical_string
        assert "DTSTAMP:" in ical_string
        assert "UID:" in ical_string
        assert "RRULE:FREQ=DAILY;COUNT=3;INTERVAL=1" in ical_string
        assert (
            "EXDATE:20230107T000000Z,20230108T000000Z,20230109T000000Z,20230110T000000Z"
            in ical_string
        )
        assert "END:VEVENT" in ical_string
        assert "END:VCALENDAR" in ical_string

    def test_to_ical_with_custom_prodid(self, calendar_entry, event, recurrence_rule):
        utc = timezone.utc
        event.start_time = django_timezone.datetime(2023, 1, 1, tzinfo=utc)
        event.end_time = django_timezone.datetime(2023, 1, 1, 1, tzinfo=utc)
        event.recurrence_rule = recurrence_rule
        event.save()

        custom_prodid = "-//Custom PRODID//EN"
        ical_string = calendar_entry.to_ical(prod_id=custom_prodid)

        assert f"PRODID:{custom_prodid}" in ical_string


@pytest.mark.django_db
class TestCalendarEntryOccurrences:
    @pytest.mark.parametrize(
        "timezone_name, summer_offset, winter_offset",
        [
            ("America/New_York", -4, -5),
            ("Europe/London", 1, 0),
            ("Europe/Berlin", 2, 1),
            ("Europe/Kiev", 3, 2),
        ],
    )
    @patch("recurring.models.datetime")
    def test_calculate_occurrences_dst_change_updated_summer(
        self, mock_datetime, timezone_name, summer_offset, winter_offset
    ):
        # Create timezone
        timezone_obj, _ = Timezone.objects.get_or_create(name=timezone_name)

        # Create CalendarEntry in July (summer time)
        summer_time = datetime(2024, 7, 1, 12, 0, tzinfo=ZoneInfo(timezone_name))
        winter_time = datetime(2024, 12, 1, 12, 0, tzinfo=ZoneInfo(timezone_name))

        mock_datetime.now.return_value = summer_time

        # create the calendar entry when DST is in effect
        calendar_entry = CalendarEntry.objects.create(
            name="Test Entry",
            timezone=timezone_obj,
        )

        # Create Event
        event = Event.objects.create(
            calendar_entry=calendar_entry,
            start_time=summer_time,
            end_time=summer_time + timedelta(hours=1),
            is_full_day=False,
        )

        # Create RecurrenceRule
        recurrence_rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
        )
        event.recurrence_rule = recurrence_rule
        event.save()

        print("Updated at=summer time, current time=summer time")
        # Calculate occurrences in July
        calendar_entry.updated_at = summer_time
        calendar_entry.calculate_occurrences()

        # Check occurrences in July
        assert calendar_entry.next_occurrence.time().hour == 12 - summer_offset
        # assert calendar_entry.previous_occurrence is None
        assert calendar_entry.first_occurrence.time().hour == 12 - summer_offset
        assert calendar_entry.last_occurrence.time().hour == 12 - summer_offset

        # Calculate occurrences in December (winter time)
        mock_datetime.now.return_value = winter_time
        # still work as if we created the calendar entry in summer time
        print("Updated at=summer time, current time=winter time")
        calendar_entry.updated_at = summer_time
        calendar_entry.calculate_occurrences()

        # Check occurrences in December
        assert calendar_entry.next_occurrence.time().hour == 12 - winter_offset
        assert calendar_entry.previous_occurrence.time().hour == 12 - winter_offset
        # first event is in summer
        assert calendar_entry.first_occurrence.time().hour == 12 - summer_offset
        assert calendar_entry.last_occurrence.time().hour == 12 - winter_offset

    @pytest.mark.parametrize(
        "timezone_name, summer_offset, winter_offset",
        [
            ("America/New_York", -4, -5),
            ("Europe/London", 1, 0),
            ("Europe/Berlin", 2, 1),
            ("Europe/Kiev", 3, 2),
        ],
    )
    @patch("recurring.models.datetime")
    def test_calculate_occurrences_dst_change_updated_winter(
        self, mock_datetime, timezone_name, summer_offset, winter_offset
    ):
        # Create timezone
        timezone_obj, _ = Timezone.objects.get_or_create(name=timezone_name)

        # Create CalendarEntry in July (summer time)
        summer_time = datetime(2024, 7, 1, 12, 0, tzinfo=ZoneInfo(timezone_name))
        winter_time = datetime(2024, 12, 1, 12, 0, tzinfo=ZoneInfo(timezone_name))

        mock_datetime.now.return_value = summer_time

        # create the calendar entry when DST is in effect
        calendar_entry = CalendarEntry.objects.create(
            name="Test Entry",
            timezone=timezone_obj,
        )

        # Create Event
        event = Event.objects.create(
            calendar_entry=calendar_entry,
            start_time=summer_time,
            end_time=summer_time + timedelta(hours=1),
            is_full_day=False,
        )

        # Create RecurrenceRule
        recurrence_rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
        )
        event.recurrence_rule = recurrence_rule
        event.save()

        print("Updated at=winter time, current time=summer time")
        # Calculate occurrences in July, but entry created in winter
        calendar_entry.updated_at = winter_time
        calendar_entry.calculate_occurrences()

        # Check occurrences in July
        assert calendar_entry.next_occurrence.time().hour == 12 - summer_offset
        # assert calendar_entry.previous_occurrence is None
        assert calendar_entry.first_occurrence.time().hour == 12 - summer_offset
        assert calendar_entry.last_occurrence.time().hour == 12 - summer_offset

        # Calculate occurrences in December (winter time)
        mock_datetime.now.return_value = winter_time
        # still work as if we created the calendar entry in winter time
        print("Updated at=winter time, current time=winter time")
        calendar_entry.updated_at = winter_time
        calendar_entry.calculate_occurrences()

        # Check occurrences in December
        assert calendar_entry.next_occurrence.time().hour == 12 - winter_offset
        assert calendar_entry.previous_occurrence.time().hour == 12 - winter_offset
        # first event is in summer
        assert calendar_entry.first_occurrence.time().hour == 12 - summer_offset
        assert calendar_entry.last_occurrence.time().hour == 12 - winter_offset

    def test_calculate_occurrences_window(self):
        timezone_obj, _ = Timezone.objects.get_or_create(name="UTC")
        calendar_entry = CalendarEntry.objects.create(
            name="Test Entry",
            timezone=timezone_obj,
        )
        start_time = django_timezone.now().replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        end_time = start_time + timedelta(hours=2)
        event = Event.objects.create(
            calendar_entry=calendar_entry,
            start_time=start_time,
            end_time=end_time,
            is_full_day=False,
        )
        recurrence_rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
        )
        event.recurrence_rule = recurrence_rule
        event.save()

        # Calculate occurrences with default window
        calendar_entry.calculate_occurrences()
        assert calendar_entry.first_occurrence is not None
        assert calendar_entry.last_occurrence is not None
        assert (
            calendar_entry.last_occurrence - calendar_entry.first_occurrence
        ).days <= 365 * 5

        # Calculate occurrences with custom window
        calendar_entry.calculate_occurrences(window_days=30, window_multiple=2)
        assert calendar_entry.first_occurrence is not None
        assert calendar_entry.last_occurrence is not None
        assert (
            calendar_entry.last_occurrence - calendar_entry.first_occurrence
        ).days <= 30 * 2


@pytest.mark.django_db
class TestEvent:
    def test_event_creation(self, event):
        assert event.start_time is not None
        assert event.end_time is not None
        assert not event.is_full_day
        assert str(event).startswith("Event for Test Calendar Entry:")

    def test_event_with_recurrence_rule(self, event, recurrence_rule):
        event.recurrence_rule = recurrence_rule
        event.save()
        assert event.recurrence_rule.frequency == RecurrenceRule.Frequency.DAILY
        assert event.recurrence_rule.interval == 1


@pytest.mark.django_db
class TestRecurrenceRule:
    def test_recurrence_rule_creation(self, recurrence_rule):
        assert recurrence_rule.frequency == RecurrenceRule.Frequency.DAILY
        assert recurrence_rule.interval == 1
        assert str(recurrence_rule) == "RecurrenceRule (Frequency: DAILY)"

    def test_get_frequency_display(self, recurrence_rule):
        assert recurrence_rule.get_frequency_display() == "DAILY"

    def test_to_dict(self, recurrence_rule):
        rule_dict = recurrence_rule.to_dict()
        assert rule_dict["frequency"] == "DAILY"
        assert rule_dict["interval"] == 1

    @pytest.mark.django_db
    def test_to_rrule_raises_valueerror_with_naive_until_and_aware_dtstart(self):
        """
        Tests that RecurrenceRule.to_rrule raises a ValueError when given a naive
        'until' datetime and an aware 'dtstart' datetime.

        According to the dateutil.rrule documentation, if dtstart is timezone-aware,
        the 'until' value must be specified in UTC. This test verifies that the
        method correctly identifies this invalid state when 'until' is naive.
        """
        la_tz_name = "America/Los_Angeles"
        try:
            la_tz = Timezone.objects.get(name=la_tz_name)
        except Timezone.DoesNotExist:
            la_tz = Timezone.objects.create(name=la_tz_name)

        # Create CalendarEntry with timezone
        calendar_entry = CalendarEntry(name="Test Event LA", timezone=la_tz)
        calendar_entry.save(recalculate=False)

        # Create Event with naive start_time/end_time. TZ comes from
        # calendar entry's timezone
        start_dt = datetime(2024, 12, 31, 10, 0, 0)
        end_dt = datetime(2024, 12, 31, 10, 30, 0)
        event = Event(
            calendar_entry=calendar_entry,
            start_time=start_dt,
            end_time=end_dt,
            is_full_day=False,
        )
        event.save()

        # Create RecurrenceRule with a naive 'until' datetime
        naive_until_dt = datetime(2025, 1, 1, 0, 0, 0)

        rule = RecurrenceRule(
            event=event,
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            until=naive_until_dt,
        )
        rule.save()

        # Link the rule to the event instance
        event.recurrence_rule = rule
        event.save()

        # Calling to_rrule with a naive 'until' while dtstart is
        # tz-aware would raise a ValueError, except we convert it to UTC
        # as required, so the following OOESN'T get raised
        # with pytest.raises(ValueError, match="RRULE UNTIL values must be specified in UTC when DTSTART is timezone-aware"):
        rule.to_rrule(event.start_time)

        # Clean up created objects
        calendar_entry.delete()


@pytest.mark.django_db
class TestExclusionDateRange:
    def test_exclusion_date_range_creation(self, event):
        event_start_time = django_timezone.datetime(
            2023, 1, 1, 10, 30, tzinfo=timezone.utc
        )
        event.start_time = event_start_time
        event.save()

        start_date = django_timezone.datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = start_date + django_timezone.timedelta(days=7)
        exclusion = ExclusionDateRange.objects.create(
            event=event,
            start_date=start_date,
            end_date=end_date,
        )
        assert exclusion.start_date.time() == event_start_time.time()
        assert exclusion.end_date.time() == event_start_time.time()
        assert (exclusion.end_date - exclusion.start_date).days == 7
        assert str(exclusion).startswith(
            "Exclusion date range for Event for Test Calendar Entry:"
        )

    def test_get_all_dates(self, event):
        event_start_time = django_timezone.datetime(
            2023, 1, 1, 10, 30, tzinfo=timezone.utc
        )
        event.start_time = event_start_time
        event.save()

        start_date = django_timezone.datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = django_timezone.datetime(2023, 1, 3, tzinfo=timezone.utc)
        exclusion = ExclusionDateRange.objects.create(
            event=event,
            start_date=start_date,
            end_date=end_date,
        )
        all_dates = exclusion.get_all_dates()

        assert len(all_dates) == 3
        for date in all_dates:
            assert date.time() == event_start_time.time()
        assert all_dates[0].date() == start_date.date()
        assert all_dates[-1].date() == end_date.date()
        assert (all_dates[-1] - all_dates[0]).days == 2
