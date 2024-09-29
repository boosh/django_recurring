import json

import pytz
from dateutil.rrule import (
    YEARLY,
    MONTHLY,
    WEEKLY,
    DAILY,
    HOURLY,
    MINUTELY,
    SECONDLY,
    MO,
    TU,
    WE,
    TH,
    FR,
    SA,
    SU,
    rrule,
    rruleset,
)
from django.db import models
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _

# created in migrations
UTC_ID = 1


class Timezone(models.Model):
    name = models.CharField(
        max_length=64, unique=True, help_text=_("The name of the timezone")
    )

    def __str__(self):
        return self.name


class RecurrenceRule(models.Model):
    class Frequency(models.IntegerChoices):
        YEARLY = YEARLY, _("YEARLY")
        MONTHLY = MONTHLY, _("MONTHLY")
        WEEKLY = WEEKLY, _("WEEKLY")
        DAILY = DAILY, _("DAILY")
        HOURLY = HOURLY, _("HOURLY")
        MINUTELY = MINUTELY, _("MINUTELY")
        SECONDLY = SECONDLY, _("SECONDLY")

    WEEKDAYS = (
        (MO.weekday, "MO"),
        (TU.weekday, "TU"),
        (WE.weekday, "WE"),
        (TH.weekday, "TH"),
        (FR.weekday, "FR"),
        (SA.weekday, "SA"),
        (SU.weekday, "SU"),
    )

    frequency = models.IntegerField(
        choices=Frequency.choices, help_text=_("The frequency of the recurrence")
    )
    interval = models.IntegerField(
        default=1, help_text=_("The interval between each freq iteration")
    )
    wkst = models.IntegerField(
        choices=WEEKDAYS, null=True, blank=True, help_text=_("The week start day")
    )
    count = models.IntegerField(
        null=True, blank=True, help_text=_("How many occurrences will be generated")
    )
    until = models.DateTimeField(
        null=True, blank=True, help_text=_("A date to repeat until")
    )
    bysetpos = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By position (BYSETPOS)")
    )
    bymonth = models.CharField(
        max_length=64, null=True, blank=True, help_text=_("By month (BYMONTH)")
    )
    bymonthday = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By month day (BYMONTHDAY)")
    )
    byyearday = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By year day (BYYEARDAY)")
    )
    byweekno = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By week number (BYWEEKNO)")
    )
    byweekday = models.CharField(
        max_length=64, null=True, blank=True, help_text=_("By weekday (BYDAY)")
    )
    byhour = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By hour (BYHOUR)")
    )
    byminute = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By minute (BYMINUTE)")
    )
    bysecond = models.CharField(
        max_length=128, null=True, blank=True, help_text=_("By second (BYSECOND)")
    )
    timezone = models.ForeignKey(
        Timezone,
        on_delete=models.SET_DEFAULT,
        default=UTC_ID,
        help_text=_("The timezone for this rule"),
    )

    def __str__(self):
        return f"RecurrenceRule (Frequency: {self.get_frequency_display()}, Timezone: {self.timezone.name})"

    def _parse_int_list(self, field):
        if field:
            return json.loads(field)
        return None

    def get_frequency_display(self):
        return self.Frequency(self.frequency).name

    def to_rrule(self):
        weekday_map = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}

        kwargs = {
            "freq": self.frequency,
            "interval": self.interval,
        }

        tz = pytz.timezone(self.timezone.name)

        if self.wkst is not None:
            kwargs["wkst"] = weekday_map[self.wkst]
        if self.count is not None:
            kwargs["count"] = self.count
        if self.until is not None:
            kwargs["until"] = (
                self.until.astimezone(tz)
                if self.until.tzinfo
                else tz.localize(self.until)
            )
        if self.bysetpos:
            kwargs["bysetpos"] = self._parse_int_list(self.bysetpos)
        if self.bymonth:
            kwargs["bymonth"] = self._parse_int_list(self.bymonth)
        if self.bymonthday:
            kwargs["bymonthday"] = self._parse_int_list(self.bymonthday)
        if self.byyearday:
            kwargs["byyearday"] = self._parse_int_list(self.byyearday)
        if self.byweekno:
            kwargs["byweekno"] = self._parse_int_list(self.byweekno)
        if self.byweekday:
            kwargs["byweekday"] = [
                weekday_map[day] for day in self._parse_int_list(self.byweekday)
            ]
        if self.byhour:
            kwargs["byhour"] = self._parse_int_list(self.byhour)
        if self.byminute:
            kwargs["byminute"] = self._parse_int_list(self.byminute)
        if self.bysecond:
            kwargs["bysecond"] = self._parse_int_list(self.bysecond)

        return rrule(**kwargs, tzinfo=tz)

    def save(self, *args, **kwargs):
        for field in [
            "bysetpos",
            "bymonth",
            "bymonthday",
            "byyearday",
            "byweekno",
            "byweekday",
            "byhour",
            "byminute",
            "bysecond",
        ]:
            value = getattr(self, field)
            if isinstance(value, list):
                setattr(self, field, json.dumps(value))
        super().save(*args, **kwargs)

    def to_dict(self):
        return {
            'frequency': self.Frequency(self.frequency).name,
            'interval': self.interval,
            'wkst': self.wkst,
            'count': self.count,
            'until': self.until.isoformat() if self.until else None,
            'bysetpos': self._parse_int_list(self.bysetpos),
            'bymonth': self._parse_int_list(self.bymonth),
            'bymonthday': self._parse_int_list(self.bymonthday),
            'byyearday': self._parse_int_list(self.byyearday),
            'byweekno': self._parse_int_list(self.byweekno),
            'byweekday': self._parse_int_list(self.byweekday),
            'byhour': self._parse_int_list(self.byhour),
            'byminute': self._parse_int_list(self.byminute),
            'bysecond': self._parse_int_list(self.bysecond),
            'timezone': self.timezone.name
        }

    @classmethod
    def from_dict(cls, data):
        rule = cls()
        rule.frequency = cls.Frequency[data['frequency']].value
        rule.interval = data.get('interval', 1)
        rule.wkst = data.get('wkst')
        rule.count = data.get('count')
        rule.until = django_timezone.parse(data['until']) if data.get('until') else None
        rule.timezone, _ = Timezone.objects.get_or_create(name=data.get('timezone', 'UTC'))

        for field in [
            'bysetpos', 'bymonth', 'bymonthday', 'byyearday', 'byweekno',
            'byweekday', 'byhour', 'byminute', 'bysecond'
        ]:
            value = data.get(field)
            if value is not None:
                setattr(rule, field, json.dumps(value))

        return rule


class RecurrenceSet(models.Model):
    name = models.CharField(
        max_length=255, help_text=_("The name of the recurrence set")
    )
    description = models.TextField(
        blank=True, help_text=_("A description of the recurrence set")
    )
    timezone = models.ForeignKey(
        Timezone,
        on_delete=models.SET_DEFAULT,
        default=UTC_ID,
        help_text=_("The timezone for this recurrence set"),
    )
    next_occurrence = models.DateTimeField(
        null=True, blank=True, help_text=_("The next occurrence of this recurrence set")
    )
    previous_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The previous occurrence of this recurrence set"),
    )

    def __str__(self):
        return f"{self.name} (Timezone: {self.timezone.name})"

    def to_rruleset(self):
        rset = rruleset()
        tz = pytz.timezone(self.timezone.name)

        for rule in self.recurrencesetrules.filter(is_exclusion=False):
            rset.rrule(rule.recurrence_rule.to_rrule())

        for rule in self.recurrencesetrules.filter(is_exclusion=True):
            rset.exrule(rule.recurrence_rule.to_rrule())

        for date in self.dates.filter(is_exclusion=False):
            rset.rdate(
                date.date.astimezone(tz) if date.date.tzinfo else tz.localize(date.date)
            )

        for date in self.dates.filter(is_exclusion=True):
            rset.exdate(
                date.date.astimezone(tz) if date.date.tzinfo else tz.localize(date.date)
            )

        return rset

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'timezone': self.timezone.name,
            'rules': [
                {
                    'is_exclusion': rule.is_exclusion,
                    'rule': rule.recurrence_rule.to_dict()
                }
                for rule in self.recurrencesetrules.all()
            ],
            'dates': [
                {
                    'date': date.date.isoformat(),
                    'is_exclusion': date.is_exclusion
                }
                for date in self.dates.all()
            ]
        }

    @classmethod
    def from_dict(cls, data):
        timezone, _ = Timezone.objects.get_or_create(name=data.get('timezone', 'UTC'))
        recurrence_set = cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            timezone=timezone
        )
        recurrence_set.save()

        for rule_data in data.get('rules', []):
            rule = RecurrenceRule.from_dict(rule_data['rule'])
            rule.save()
            RecurrenceSetRule.objects.create(
                recurrence_set=recurrence_set,
                recurrence_rule=rule,
                is_exclusion=rule_data['is_exclusion']
            )

        for date_data in data.get('dates', []):
            RecurrenceDate.objects.create(
                recurrence_set=recurrence_set,
                date=django_timezone.parse(date_data['date']),
                is_exclusion=date_data['is_exclusion']
            )

        return recurrence_set

    def recalculate_occurrences(self):
        try:
            rruleset = self.to_rruleset()
            now = django_timezone.now()
            tz = pytz.timezone(self.timezone.name)

            # Calculate next occurrence
            next_occurrences = list(rruleset.after(now, inc=False, count=1))
            self.next_occurrence = (
                next_occurrences[0].astimezone(tz) if next_occurrences else None
            )

            # Calculate previous occurrence
            prev_occurrences = list(rruleset.before(now, inc=False, count=1))
            self.previous_occurrence = (
                prev_occurrences[0].astimezone(tz) if prev_occurrences else None
            )

            self.save()
        except Exception as e:
            print(
                f"Error recalculating occurrences for RecurrenceSet {self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalculate_occurrences()


class RecurrenceSetRule(models.Model):
    recurrence_set = models.ForeignKey(
        RecurrenceSet,
        on_delete=models.CASCADE,
        related_name="recurrencesetrules",
        help_text=_("The recurrence set this rule belongs to"),
    )
    recurrence_rule = models.ForeignKey(
        RecurrenceRule, on_delete=models.CASCADE, help_text=_("The recurrence rule")
    )
    is_exclusion = models.BooleanField(
        default=False, help_text=_("Whether this rule is an exclusion rule")
    )

    def __str__(self):
        rule_type = "Exclusion" if self.is_exclusion else "Inclusion"
        return f"{rule_type} Rule for {self.recurrence_set}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recurrence_set.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        recurrence_set = self.recurrence_set
        super().delete(*args, **kwargs)
        recurrence_set.recalculate_occurrences()


class RecurrenceDate(models.Model):
    recurrence_set = models.ForeignKey(
        RecurrenceSet,
        on_delete=models.CASCADE,
        related_name="dates",
        help_text=_("The recurrence set this date belongs to"),
    )
    date = models.DateTimeField(help_text=_("The date of recurrence or exclusion"))
    is_exclusion = models.BooleanField(
        default=False, help_text=_("Whether this date is an exclusion date")
    )

    def __str__(self):
        date_type = "Exclusion" if self.is_exclusion else "Inclusion"
        return f"{date_type} Date for {self.recurrence_set}: {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recurrence_set.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        recurrence_set = self.recurrence_set
        super().delete(*args, **kwargs)
        recurrence_set.recalculate_occurrences()
