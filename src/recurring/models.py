import json

import pytz
from dateutil.rrule import (
    YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY,
    MO, TU, WE, TH, FR, SA, SU, rrule, rruleset
)
from django.db import models
from icalendar import Event, vRecur, vDDDTypes

# todo - create this in migrations
UTC_ID = 1


class Timezone(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class RecurrenceRule(models.Model):
    FREQUENCIES = (
        (YEARLY, 'YEARLY'),
        (MONTHLY, 'MONTHLY'),
        (WEEKLY, 'WEEKLY'),
        (DAILY, 'DAILY'),
        (HOURLY, 'HOURLY'),
        (MINUTELY, 'MINUTELY'),
        (SECONDLY, 'SECONDLY'),
    )

    WEEKDAYS = (
        (MO.weekday, 'MO'),
        (TU.weekday, 'TU'),
        (WE.weekday, 'WE'),
        (TH.weekday, 'TH'),
        (FR.weekday, 'FR'),
        (SA.weekday, 'SA'),
        (SU.weekday, 'SU'),
    )

    frequency = models.IntegerField(choices=FREQUENCIES)
    interval = models.IntegerField(default=1)
    wkst = models.IntegerField(choices=WEEKDAYS, null=True, blank=True)
    count = models.IntegerField(null=True, blank=True)
    until = models.DateTimeField(null=True, blank=True)
    bysetpos = models.CharField(max_length=128, null=True, blank=True)
    bymonth = models.CharField(max_length=64, null=True, blank=True)
    bymonthday = models.CharField(max_length=128, null=True, blank=True)
    byyearday = models.CharField(max_length=128, null=True, blank=True)
    byweekno = models.CharField(max_length=128, null=True, blank=True)
    byweekday = models.CharField(max_length=64, null=True, blank=True)
    byhour = models.CharField(max_length=128, null=True, blank=True)
    byminute = models.CharField(max_length=128, null=True, blank=True)
    bysecond = models.CharField(max_length=128, null=True, blank=True)
    timezone = models.ForeignKey(Timezone, on_delete=models.SET_DEFAULT, default=UTC_ID)

    def __str__(self):
        return f"RecurrenceRule (Frequency: {self.get_frequency_display()}, Timezone: {self.timezone.name})"

    def _parse_int_list(self, field):
        if field:
            return json.loads(field)
        return None

    def to_rrule(self):
        weekday_map = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}

        kwargs = {
            'freq': self.frequency,
            'interval': self.interval,
        }

        tz = pytz.timezone(self.timezone.name)

        if self.wkst is not None:
            kwargs['wkst'] = weekday_map[self.wkst]
        if self.count is not None:
            kwargs['count'] = self.count
        if self.until is not None:
            kwargs['until'] = self.until.astimezone(tz)
        if self.bysetpos:
            kwargs['bysetpos'] = self._parse_int_list(self.bysetpos)
        if self.bymonth:
            kwargs['bymonth'] = self._parse_int_list(self.bymonth)
        if self.bymonthday:
            kwargs['bymonthday'] = self._parse_int_list(self.bymonthday)
        if self.byyearday:
            kwargs['byyearday'] = self._parse_int_list(self.byyearday)
        if self.byweekno:
            kwargs['byweekno'] = self._parse_int_list(self.byweekno)
        if self.byweekday:
            kwargs['byweekday'] = [weekday_map[day] for day in self._parse_int_list(self.byweekday)]
        if self.byhour:
            kwargs['byhour'] = self._parse_int_list(self.byhour)
        if self.byminute:
            kwargs['byminute'] = self._parse_int_list(self.byminute)
        if self.bysecond:
            kwargs['bysecond'] = self._parse_int_list(self.bysecond)

        return rrule(**kwargs, tzinfo=tz)

    def save(self, *args, **kwargs):
        for field in ['bysetpos', 'bymonth', 'bymonthday', 'byyearday', 'byweekno', 'byweekday', 'byhour', 'byminute',
                      'bysecond']:
            value = getattr(self, field)
            if isinstance(value, list):
                setattr(self, field, json.dumps(value))
        super().save(*args, **kwargs)

    def to_ical(self):
        recur = vRecur()
        recur['FREQ'] = [freq for freq, name in self.FREQUENCIES if freq == self.frequency][0]
        recur['INTERVAL'] = self.interval

        if self.wkst is not None:
            recur['WKST'] = [name for day, name in self.WEEKDAYS if day == self.wkst][0]
        if self.count is not None:
            recur['COUNT'] = self.count
        if self.until is not None:
            recur['UNTIL'] = vDDDTypes(self.until.astimezone(pytz.UTC))

        for field in ['BYSETPOS', 'BYMONTH', 'BYMONTHDAY', 'BYYEARDAY', 'BYWEEKNO', 'BYDAY', 'BYHOUR', 'BYMINUTE',
                      'BYSECOND']:
            value = getattr(self, field.lower())
            if value:
                recur[field] = self._parse_int_list(value)

        return recur.to_ical().decode('utf-8')

    @classmethod
    def from_ical(cls, ical_string, timezone='UTC'):
        recur = vRecur.from_ical(ical_string)
        rule = cls()

        rule.frequency = [freq for freq, name in cls.FREQUENCIES if name == recur['FREQ'][0]][0]
        rule.interval = recur.get('INTERVAL', 1)
        rule.timezone, _ = Timezone.objects.get_or_create(name=timezone)

        if 'WKST' in recur:
            rule.wkst = [day for day, name in cls.WEEKDAYS if name == recur['WKST']][0]
        if 'COUNT' in recur:
            rule.count = recur['COUNT']
        if 'UNTIL' in recur:
            tz = pytz.timezone(timezone)
            rule.until = recur['UNTIL'].dt.astimezone(tz)

        for field in ['BYSETPOS', 'BYMONTH', 'BYMONTHDAY', 'BYYEARDAY', 'BYWEEKNO', 'BYDAY', 'BYHOUR', 'BYMINUTE',
                      'BYSECOND']:
            if field in recur:
                setattr(rule, field.lower(), json.dumps(recur[field]))

        return rule


class RecurrenceSet(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    timezone = models.ForeignKey(Timezone, on_delete=models.SET_DEFAULT, default=UTC_ID)

    def __str__(self):
        return f"{self.name} (Timezone: {self.timezone.name})"

    def to_rruleset(self):
        rset = rruleset()
        tz = pytz.timezone(self.timezone.name)

        for rule in self.rules.filter(is_exclusion=False):
            rset.rrule(rule.recurrence_rule.to_rrule())

        for rule in self.rules.filter(is_exclusion=True):
            rset.exrule(rule.recurrence_rule.to_rrule())

        for date in self.dates.filter(is_exclusion=False):
            rset.rdate(date.date.astimezone(tz))

        for date in self.dates.filter(is_exclusion=True):
            rset.exdate(date.date.astimezone(tz))

        return rset

    def to_ical(self):
        event = Event()
        for rule in self.rules.filter(is_exclusion=False):
            event.add('rrule', rule.recurrence_rule.to_ical())
        for rule in self.rules.filter(is_exclusion=True):
            event.add('exrule', rule.recurrence_rule.to_ical())
        for date in self.dates.filter(is_exclusion=False):
            event.add('rdate', date.date.astimezone(pytz.UTC))
        for date in self.dates.filter(is_exclusion=True):
            event.add('exdate', date.date.astimezone(pytz.UTC))
        event.add('tzid', self.timezone)
        return event.to_ical().decode('utf-8')

    @classmethod
    def from_ical(cls, ical_string):
        event = Event.from_ical(ical_string)
        timezone_name = str(event.get('tzid', 'UTC'))
        timezone, _ = Timezone.objects.get_or_create(name=timezone_name)
        recurrence_set = cls(timezone=timezone)
        recurrence_set.save()  # Save to generate an ID

        for rrule in event.get('rrule', []):
            rule = RecurrenceRule.from_ical(rrule.to_ical(), timezone=timezone_name)
            rule.save()
            RecurrenceSetRule.objects.create(recurrence_set=recurrence_set, recurrence_rule=rule, is_exclusion=False)

        for exrule in event.get('exrule', []):
            rule = RecurrenceRule.from_ical(exrule.to_ical(), timezone=timezone_name)
            rule.save()
            RecurrenceSetRule.objects.create(recurrence_set=recurrence_set, recurrence_rule=rule, is_exclusion=True)

        tz = pytz.timezone(timezone_name)
        for rdate in event.get('rdate', []):
            RecurrenceDate.objects.create(recurrence_set=recurrence_set, date=rdate.dt.astimezone(tz),
                                          is_exclusion=False)

        for exdate in event.get('exdate', []):
            RecurrenceDate.objects.create(recurrence_set=recurrence_set, date=exdate.dt.astimezone(tz),
                                          is_exclusion=True)

        return recurrence_set


class RecurrenceSetRule(models.Model):
    recurrence_set = models.ForeignKey(RecurrenceSet, on_delete=models.CASCADE, related_name='rules')
    recurrence_rule = models.ForeignKey(RecurrenceRule, on_delete=models.CASCADE)
    is_exclusion = models.BooleanField(default=False)

    def __str__(self):
        rule_type = "Exclusion" if self.is_exclusion else "Inclusion"
        return f"{rule_type} Rule for {self.recurrence_set}"


class RecurrenceDate(models.Model):
    recurrence_set = models.ForeignKey(RecurrenceSet, on_delete=models.CASCADE, related_name='dates')
    date = models.DateTimeField()
    is_exclusion = models.BooleanField(default=False)

    def __str__(self):
        date_type = "Exclusion" if self.is_exclusion else "Inclusion"
        return f"{date_type} Date for {self.recurrence_set}: {self.date}"
