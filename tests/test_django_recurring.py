import json
from datetime import timedelta

import pytz
from dateutil.rrule import DAILY, WEEKLY, MONTHLY, YEARLY, MO, WE, FR
from django.test import TestCase
from django.utils import timezone
from recurring.models import Timezone, RecurrenceRule, RecurrenceSet, RecurrenceSetRule, RecurrenceDate


class TimezoneModelTest(TestCase):
    def test_timezone_creation(self):
        timezone = Timezone.objects.create(name="America/New_York")
        self.assertEqual(str(timezone), "America/New_York")


class RecurrenceRuleModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")

    def test_recurrence_rule_creation(self):
        rule = RecurrenceRule.objects.create(
            frequency=DAILY,
            interval=1,
            timezone=self.timezone
        )
        self.assertEqual(str(rule), "RecurrenceRule (Frequency: DAILY, Timezone: UTC)")

    def test_to_rrule(self):
        rule = RecurrenceRule.objects.create(
            frequency=WEEKLY,
            interval=2,
            byweekday=json.dumps([MO.weekday, WE.weekday, FR.weekday]),
            timezone=self.timezone
        )
        rrule_obj = rule.to_rrule()
        self.assertEqual(rrule_obj._freq, WEEKLY)
        self.assertEqual(rrule_obj._interval, 2)
        self.assertEqual(rrule_obj._byweekday, [MO, WE, FR])

    def test_to_ical(self):
        rule = RecurrenceRule.objects.create(
            frequency=MONTHLY,
            interval=1,
            bymonthday=json.dumps([1, 15]),
            timezone=self.timezone
        )
        ical_string = rule.to_ical()
        self.assertIn("FREQ=MONTHLY", ical_string)
        self.assertIn("INTERVAL=1", ical_string)
        self.assertIn("BYMONTHDAY=1,15", ical_string)

    def test_from_ical(self):
        ical_string = "FREQ=DAILY;INTERVAL=2;COUNT=10"
        rule = RecurrenceRule.from_ical(ical_string)
        self.assertEqual(rule.frequency, DAILY)
        self.assertEqual(rule.interval, 2)
        self.assertEqual(rule.count, 10)

    def test_complex_rrule(self):
        rule = RecurrenceRule.objects.create(
            frequency=YEARLY,
            interval=1,
            bymonth=json.dumps([3, 6, 9, 12]),
            byweekday=json.dumps([MO.weekday, FR.weekday]),
            bysetpos=json.dumps([1, -1]),
            timezone=self.timezone
        )
        rrule_obj = rule.to_rrule()
        self.assertEqual(rrule_obj._freq, YEARLY)
        self.assertEqual(rrule_obj._bymonth, [3, 6, 9, 12])
        self.assertEqual(rrule_obj._byweekday, [MO, FR])
        self.assertEqual(rrule_obj._bysetpos, [1, -1])

    def test_rrule_with_until(self):
        until_date = timezone.now() + timedelta(days=30)
        rule = RecurrenceRule.objects.create(
            frequency=DAILY,
            interval=1,
            until=until_date,
            timezone=self.timezone
        )
        rrule_obj = rule.to_rrule()
        self.assertEqual(rrule_obj._until, until_date.replace(tzinfo=pytz.UTC))


class RecurrenceSetModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(
            name="Test Set",
            description="A test recurrence set",
            timezone=self.timezone
        )

    def test_recurrence_set_creation(self):
        self.assertEqual(str(self.recurrence_set), "Test Set (Timezone: UTC)")

    def test_to_rruleset(self):
        rule1 = RecurrenceRule.objects.create(frequency=DAILY, interval=1, timezone=self.timezone)
        rule2 = RecurrenceRule.objects.create(frequency=WEEKLY, interval=1, timezone=self.timezone)
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule1)
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule2, is_exclusion=True)

        rruleset = self.recurrence_set.to_rruleset()
        self.assertEqual(len(rruleset._rrule), 1)
        self.assertEqual(len(rruleset._exrule), 1)

    def test_recalculate_occurrences(self):
        rule = RecurrenceRule.objects.create(frequency=DAILY, interval=1, timezone=self.timezone)
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule)

        now = timezone.now()
        self.recurrence_set.recalculate_occurrences()

        self.assertIsNotNone(self.recurrence_set.next_occurrence)
        self.assertGreater(self.recurrence_set.next_occurrence, now)

    def test_to_ical(self):
        rule = RecurrenceRule.objects.create(frequency=DAILY, interval=1, timezone=self.timezone)
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule)

        ical_string = self.recurrence_set.to_ical()
        self.assertIn("RRULE:FREQ=DAILY;INTERVAL=1", ical_string)
        self.assertIn("TZID:UTC", ical_string)

    def test_from_ical(self):
        ical_string = """BEGIN:VEVENT
RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR
EXDATE:20230101T000000Z
RDATE:20230102T000000Z
TZID:America/New_York
END:VEVENT"""

        recurrence_set = RecurrenceSet.from_ical(ical_string)
        self.assertEqual(recurrence_set.timezone.name, "America/New_York")
        self.assertEqual(recurrence_set.recurrencesetrules.count(), 1)
        self.assertEqual(recurrence_set.dates.count(), 2)

    def test_complex_recurrence_set(self):
        rule1 = RecurrenceRule.objects.create(
            frequency=WEEKLY,
            interval=1,
            byweekday=json.dumps([MO.weekday, WE.weekday, FR.weekday]),
            timezone=self.timezone
        )
        rule2 = RecurrenceRule.objects.create(
            frequency=MONTHLY,
            interval=1,
            bymonthday=json.dumps([1, 15]),
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule1)
        RecurrenceSetRule.objects.create(recurrence_set=self.recurrence_set, recurrence_rule=rule2)

        now = timezone.now()
        RecurrenceDate.objects.create(recurrence_set=self.recurrence_set, date=now + timedelta(days=1))
        RecurrenceDate.objects.create(recurrence_set=self.recurrence_set, date=now + timedelta(days=2),
                                      is_exclusion=True)

        self.recurrence_set.recalculate_occurrences()

        self.assertIsNotNone(self.recurrence_set.next_occurrence)
        self.assertIsNotNone(self.recurrence_set.previous_occurrence)

        rruleset = self.recurrence_set.to_rruleset()
        self.assertEqual(len(rruleset._rrule), 2)
        self.assertEqual(len(rruleset._rdate), 1)
        self.assertEqual(len(rruleset._exdate), 1)


class RecurrenceSetRuleModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(name="Test Set", timezone=self.timezone)
        self.rule = RecurrenceRule.objects.create(frequency=DAILY, interval=1, timezone=self.timezone)

    def test_recurrence_set_rule_creation(self):
        set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=self.rule
        )
        self.assertEqual(str(set_rule), f"Inclusion Rule for {self.recurrence_set}")

    def test_recurrence_set_rule_exclusion(self):
        set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=self.rule,
            is_exclusion=True
        )
        self.assertEqual(str(set_rule), f"Exclusion Rule for {self.recurrence_set}")

    def test_recurrence_set_rule_save_and_delete(self):
        set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=self.rule
        )
        self.assertIsNotNone(self.recurrence_set.next_occurrence)

        set_rule.delete()
        self.recurrence_set.refresh_from_db()
        self.assertIsNone(self.recurrence_set.next_occurrence)


class RecurrenceDateModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(name="Test Set", timezone=self.timezone)

    def test_recurrence_date_creation(self):
        date = timezone.now()
        recurrence_date = RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=date
        )
        self.assertEqual(str(recurrence_date), f"Inclusion Date for {self.recurrence_set}: {date}")

    def test_recurrence_date_exclusion(self):
        date = timezone.now()
        recurrence_date = RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=date,
            is_exclusion=True
        )
        self.assertEqual(str(recurrence_date), f"Exclusion Date for {self.recurrence_set}: {date}")

    def test_recurrence_date_save_and_delete(self):
        date = timezone.now() + timedelta(days=1)
        recurrence_date = RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=date
        )
        self.recurrence_set.refresh_from_db()
        self.assertEqual(self.recurrence_set.next_occurrence, date)

        recurrence_date.delete()
        self.recurrence_set.refresh_from_db()
        self.assertIsNone(self.recurrence_set.next_occurrence)
