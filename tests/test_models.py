from dateutil.rrule import WEEKLY
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
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )
        self.assertEqual(str(rule), "RecurrenceRule (Frequency: DAILY, Timezone: UTC)")

    def test_recurrence_rule_to_rrule(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.WEEKLY,
            interval=2,
            byweekday='[0, 2, 4]',  # Monday, Wednesday, Friday
            timezone=self.timezone
        )
        rrule_obj = rule.to_rrule()
        self.assertEqual(rrule_obj._freq, WEEKLY)
        self.assertEqual(rrule_obj._interval, 2)
        self.assertEqual(len(rrule_obj._byweekday), 3)

    def test_recurrence_rule_to_ical(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.MONTHLY,
            interval=1,
            bymonthday='[1, 15]',
            timezone=self.timezone
        )
        ical_string = rule.to_ical()
        self.assertIn('FREQ=MONTHLY', ical_string)
        self.assertIn('INTERVAL=1', ical_string)
        self.assertIn('BYMONTHDAY=1,15', ical_string)

    def test_recurrence_rule_from_ical(self):
        ical_string = 'FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYDAY=MO'
        rule = RecurrenceRule.from_ical(ical_string, timezone="UTC")
        self.assertEqual(rule.frequency, RecurrenceRule.Frequency.YEARLY)
        self.assertEqual(rule.interval, 1)
        self.assertEqual(rule.bymonth, '[1]')
        self.assertEqual(rule.byweekday, '[0]')  # Monday is 0


class RecurrenceSetModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(
            name="Test Set",
            description="Test Description",
            timezone=self.timezone
        )

    def test_recurrence_set_creation(self):
        self.assertEqual(str(self.recurrence_set), "Test Set (Timezone: UTC)")

    def test_recurrence_set_to_rruleset(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=rule,
            is_exclusion=False
        )
        RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=timezone.now(),
            is_exclusion=False
        )

        rruleset = self.recurrence_set.to_rruleset()
        self.assertEqual(len(rruleset._rrule), 1)
        self.assertEqual(len(rruleset._rdate), 1)

    def test_recurrence_set_to_ical(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.WEEKLY,
            interval=1,
            byweekday='[0, 4]',  # Monday and Friday
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=rule,
            is_exclusion=False
        )

        ical_string = self.recurrence_set.to_ical()
        self.assertIn('RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,FR', ical_string)
        self.assertIn('TZID:UTC', ical_string)

    def test_recurrence_set_from_ical(self):
        ical_string = """BEGIN:VEVENT
RRULE:FREQ=DAILY;INTERVAL=1
RDATE:20230101T120000Z
EXDATE:20230102T120000Z
TZID:America/New_York
END:VEVENT"""
        recurrence_set = RecurrenceSet.from_ical(ical_string)
        self.assertEqual(recurrence_set.timezone.name, "America/New_York")
        self.assertEqual(recurrence_set.recurrencesetrules.count(), 1)
        self.assertEqual(recurrence_set.dates.count(), 2)

    def test_recurrence_set_recalculate_occurrences(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=rule,
            is_exclusion=False
        )

        self.recurrence_set.recalculate_occurrences()
        self.assertIsNotNone(self.recurrence_set.next_occurrence)
        self.assertIsNone(self.recurrence_set.previous_occurrence)


class RecurrenceSetRuleModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(
            name="Test Set",
            description="Test Description",
            timezone=self.timezone
        )
        self.rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )

    def test_recurrence_set_rule_creation(self):
        set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=self.rule,
            is_exclusion=False
        )
        self.assertEqual(str(set_rule), f"Inclusion Rule for {self.recurrence_set}")

    def test_recurrence_set_rule_deletion_triggers_recalculation(self):
        set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=self.rule,
            is_exclusion=False
        )
        self.recurrence_set.recalculate_occurrences()
        initial_next_occurrence = self.recurrence_set.next_occurrence

        set_rule.delete()
        self.recurrence_set.refresh_from_db()
        self.assertNotEqual(initial_next_occurrence, self.recurrence_set.next_occurrence)


class RecurrenceDateModelTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(
            name="Test Set",
            description="Test Description",
            timezone=self.timezone
        )

    def test_recurrence_date_creation(self):
        date = RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=timezone.now(),
            is_exclusion=False
        )
        self.assertIn("Inclusion Date for Test Set", str(date))

    def test_recurrence_date_deletion_triggers_recalculation(self):
        date = RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=timezone.now(),
            is_exclusion=False
        )
        self.recurrence_set.recalculate_occurrences()
        initial_next_occurrence = self.recurrence_set.next_occurrence

        date.delete()
        self.recurrence_set.refresh_from_db()
        self.assertNotEqual(initial_next_occurrence, self.recurrence_set.next_occurrence)
