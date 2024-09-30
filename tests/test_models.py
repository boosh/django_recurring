import pytest
from dateutil.rrule import rrule, DAILY
from django.utils import timezone as django_timezone

from recurring.models import Timezone, RecurrenceRule, RecurrenceRuleDateRange, RecurrenceSet, RecurrenceSetRule


@pytest.fixture
def timezone_obj():
    return Timezone.objects.get_or_create(name="UTC")[0]

@pytest.fixture
def recurrence_rule(timezone_obj):
    return RecurrenceRule.objects.create(
        frequency=DAILY,
        interval=1,
        timezone=timezone_obj
    )

@pytest.fixture
def recurrence_set(timezone_obj):
    return RecurrenceSet.objects.create(
        name="Test Recurrence Set",
        description="A test recurrence set",
        timezone=timezone_obj
    )

@pytest.mark.django_db
class TestTimezone:
    def test_timezone_creation(self, timezone_obj):
        assert timezone_obj.name == "UTC"
        assert str(timezone_obj) == "UTC"

@pytest.mark.django_db
class TestRecurrenceRule:
    def test_recurrence_rule_creation(self, recurrence_rule):
        assert recurrence_rule.frequency == DAILY
        assert recurrence_rule.interval == 1
        assert str(recurrence_rule) == "RecurrenceRule (Frequency: DAILY, Timezone: UTC)"

    def test_get_frequency_display(self, recurrence_rule):
        assert recurrence_rule.get_frequency_display() == "DAILY"

    def test_to_rrule(self, recurrence_rule):
        start_date = django_timezone.now()
        end_date = start_date + django_timezone.timedelta(days=7)
        rrule_obj = recurrence_rule.to_rrule(start_date, end_date)
        assert isinstance(rrule_obj, rrule)
        assert rrule_obj.freq == DAILY

    def test_to_dict(self, recurrence_rule):
        rule_dict = recurrence_rule.to_dict()
        assert rule_dict['frequency'] == 'DAILY'
        assert rule_dict['interval'] == 1
        assert rule_dict['timezone'] == 'UTC'

@pytest.mark.django_db
class TestRecurrenceRuleDateRange:
    def test_date_range_creation(self, recurrence_rule):
        start_date = django_timezone.now()
        end_date = start_date + django_timezone.timedelta(days=7)
        date_range = RecurrenceRuleDateRange.objects.create(
            recurrence_rule=recurrence_rule,
            start_date=start_date,
            end_date=end_date,
            is_exclusion=False
        )
        assert date_range.start_date == start_date
        assert date_range.end_date == end_date
        assert not date_range.is_exclusion
        assert str(date_range).startswith("Inclusion Date Range for RecurrenceRule")

@pytest.mark.django_db
class TestRecurrenceSet:
    def test_recurrence_set_creation(self, recurrence_set):
        assert recurrence_set.name == "Test Recurrence Set"
        assert recurrence_set.description == "A test recurrence set"
        assert str(recurrence_set) == "Test Recurrence Set (Timezone: UTC)"

    def test_to_rruleset(self, recurrence_set, recurrence_rule):
        RecurrenceSetRule.objects.create(
            recurrence_set=recurrence_set,
            recurrence_rule=recurrence_rule,
            is_exclusion=False
        )
        rruleset = recurrence_set.to_rruleset()
        assert len(rruleset._rrule) == 1
        assert len(rruleset._exrule) == 0

    def test_to_dict(self, recurrence_set, recurrence_rule):
        RecurrenceSetRule.objects.create(
            recurrence_set=recurrence_set,
            recurrence_rule=recurrence_rule,
            is_exclusion=False
        )
        recurrence_set_dict = recurrence_set.to_dict()
        assert recurrence_set_dict['name'] == "Test Recurrence Set"
        assert recurrence_set_dict['description'] == "A test recurrence set"
        assert recurrence_set_dict['timezone'] == "UTC"
        assert len(recurrence_set_dict['rules']) == 1

    def test_from_dict(self, recurrence_set):
        data = {
            'rules': [
                {
                    'is_exclusion': False,
                    'rule': {
                        'frequency': 'DAILY',
                        'interval': 1,
                        'byweekday': ['MO', 'WE', 'FR']
                    },
                    'date_ranges': [
                        {
                            'start_date': '2023-01-01T00:00:00+00:00',
                            'end_date': '2023-12-31T23:59:59+00:00',
                            'is_exclusion': False
                        }
                    ]
                }
            ]
        }
        recurrence_set.from_dict(data)
        assert recurrence_set.recurrencesetrules.count() == 1
        rule = recurrence_set.recurrencesetrules.first().recurrence_rule
        assert rule.frequency == DAILY
        assert rule.interval == 1
        assert rule.byweekday == ['MO', 'WE', 'FR']
        assert rule.date_ranges.count() == 1

    def test_recalculate_occurrences(self, recurrence_set, recurrence_rule):
        RecurrenceSetRule.objects.create(
            recurrence_set=recurrence_set,
            recurrence_rule=recurrence_rule,
            is_exclusion=False
        )
        RecurrenceRuleDateRange.objects.create(
            recurrence_rule=recurrence_rule,
            start_date=django_timezone.now(),
            end_date=django_timezone.now() + django_timezone.timedelta(days=30),
            is_exclusion=False
        )
        recurrence_set.recalculate_occurrences()
        assert recurrence_set.next_occurrence is not None
        assert recurrence_set.previous_occurrence is None

@pytest.mark.django_db
class TestRecurrenceSetRule:
    def test_recurrence_set_rule_creation(self, recurrence_set, recurrence_rule):
        recurrence_set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=recurrence_set,
            recurrence_rule=recurrence_rule,
            is_exclusion=False
        )
        assert not recurrence_set_rule.is_exclusion
        assert str(recurrence_set_rule) == "Inclusion Rule for Test Recurrence Set (Timezone: UTC)"

    def test_recurrence_set_rule_deletion(self, recurrence_set, recurrence_rule):
        recurrence_set_rule = RecurrenceSetRule.objects.create(
            recurrence_set=recurrence_set,
            recurrence_rule=recurrence_rule,
            is_exclusion=False
        )
        rule_id = recurrence_rule.id
        recurrence_set_rule.delete()
        assert not RecurrenceRule.objects.filter(id=rule_id).exists()
