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
    bysetpos = models.JSONField(
        null=True, blank=True, help_text=_("By position (BYSETPOS)")
    )
    bymonth = models.JSONField(
        null=True, blank=True, help_text=_("By month (BYMONTH)")
    )
    bymonthday = models.JSONField(
        null=True, blank=True, help_text=_("By month day (BYMONTHDAY)")
    )
    byyearday = models.JSONField(
        null=True, blank=True, help_text=_("By year day (BYYEARDAY)")
    )
    byweekno = models.JSONField(
        null=True, blank=True, help_text=_("By week number (BYWEEKNO)")
    )
    byweekday = models.JSONField(
        null=True, blank=True, help_text=_("By weekday (BYDAY)")
    )
    byhour = models.JSONField(
        null=True, blank=True, help_text=_("By hour (BYHOUR)")
    )
    byminute = models.JSONField(
        null=True, blank=True, help_text=_("By minute (BYMINUTE)")
    )
    bysecond = models.JSONField(
        null=True, blank=True, help_text=_("By second (BYSECOND)")
    )
    timezone = models.ForeignKey(
        Timezone,
        on_delete=models.SET_DEFAULT,
        default=UTC_ID,
        help_text=_("The timezone for this rule"),
    )

    def __str__(self):
        return f"RecurrenceRule (Frequency: {self.get_frequency_display()}, Timezone: {self.timezone.name})"

    def get_frequency_display(self):
        return self.Frequency(self.frequency).name

    def to_rrule(self, start_date, end_date):
        weekday_map = {'MO': MO, 'TU': TU, 'WE': WE, 'TH': TH, 'FR': FR, 'SA': SA, 'SU': SU}

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
            kwargs["until"] = min(
                self.until.astimezone(tz) if self.until.tzinfo else tz.localize(self.until),
                end_date
            )
        if self.bysetpos:
            kwargs["bysetpos"] = self.bysetpos
        if self.bymonth:
            kwargs["bymonth"] = self.bymonth
        if self.bymonthday:
            kwargs["bymonthday"] = self.bymonthday
        if self.byyearday:
            kwargs["byyearday"] = self.byyearday
        if self.byweekno:
            kwargs["byweekno"] = self.byweekno
        if self.byweekday:
            kwargs["byweekday"] = [weekday_map[day] for day in self.byweekday]
        if self.byhour:
            kwargs["byhour"] = self.byhour
        if self.byminute:
            kwargs["byminute"] = self.byminute
        if self.bysecond:
            kwargs["bysecond"] = self.bysecond

        return rrule(dtstart=start_date.astimezone(tz), **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'frequency': self.Frequency(self.frequency).name,
            'interval': self.interval,
            'wkst': self.wkst,
            'count': self.count,
            'until': self.until.isoformat() if self.until else None,
            'bysetpos': self.bysetpos,
            'bymonth': self.bymonth,
            'bymonthday': self.bymonthday,
            'byyearday': self.byyearday,
            'byweekno': self.byweekno,
            'byweekday': self.byweekday,
            'byhour': self.byhour,
            'byminute': self.byminute,
            'bysecond': self.bysecond,
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
                setattr(rule, field, value)

        return rule


class RecurrenceRuleDateRange(models.Model):
    recurrence_rule = models.ForeignKey(
        RecurrenceRule,
        on_delete=models.CASCADE,
        related_name="date_ranges",
        help_text=_("The recurrence rule this date range belongs to"),
    )
    start_date = models.DateTimeField(help_text=_("The start date of the date range"))
    end_date = models.DateTimeField(help_text=_("The end date of the date range"))
    is_exclusion = models.BooleanField(
        default=False, help_text=_("Whether this date range is an exclusion")
    )

    def __str__(self):
        range_type = "Exclusion" if self.is_exclusion else "Inclusion"
        return f"{range_type} Date Range for {self.recurrence_rule}: {self.start_date} to {self.end_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        recurrence_set_rule = RecurrenceSetRule.objects.filter(recurrence_rule=self.recurrence_rule).first()
        if recurrence_set_rule:
            recurrence_set_rule.recurrence_set.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        recurrence_set_rule = RecurrenceSetRule.objects.filter(recurrence_rule=self.recurrence_rule).first()
        super().delete(*args, **kwargs)
        if recurrence_set_rule:
            recurrence_set_rule.recurrence_set.recalculate_occurrences()


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

        for rule in self.recurrencesetrules.all():
            for date_range in rule.recurrence_rule.date_ranges.all():
                rrule_obj = rule.recurrence_rule.to_rrule(date_range.start_date, date_range.end_date)
                if date_range.is_exclusion:
                    rset.exrule(rrule_obj)
                else:
                    rset.rrule(rrule_obj)

        return rset

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'timezone': self.timezone.name,
            'rules': [
                {
                    'is_exclusion': rule.is_exclusion,
                    'rule': rule.recurrence_rule.to_dict(),
                }
                for rule in self.recurrencesetrules.all()
            ]
        }

    def recalculate_occurrences(self):
        try:
            rruleset = self.to_rruleset()
            now = django_timezone.now()
            tz = pytz.timezone(self.timezone.name)

            # Calculate next occurrence
            next_occurrence = rruleset.after(now, inc=False)
            self.next_occurrence = next_occurrence.astimezone(tz) if next_occurrence else None

            # Calculate previous occurrence
            prev_occurrence = rruleset.before(now, inc=False)
            self.previous_occurrence = prev_occurrence.astimezone(tz) if prev_occurrence else None
        except Exception as e:
            print(
                f"Error recalculating occurrences for RecurrenceSet {self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        recalculate = kwargs.pop('recalculate', True)
        super().save(*args, **kwargs)
        if recalculate:
            self.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        # Delete related RecurrenceRules and RecurrenceRuleDateRanges
        for rule in self.recurrencesetrules.all():
            rule.recurrence_rule.date_ranges.all().delete()
            rule.recurrence_rule.delete()
        super().delete(*args, **kwargs)


class RecurrenceSetRule(models.Model):
    recurrence_set = models.ForeignKey(
        RecurrenceSet,
        on_delete=models.CASCADE,
        related_name="recurrencesetrules",
        help_text=_("The recurrence set this rule belongs to"),
    )
    recurrence_rule = models.OneToOneField(
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
        self.recurrence_set.save(recalculate=True)

    def delete(self, *args, **kwargs):
        recurrence_set = self.recurrence_set
        self.recurrence_rule.delete()  # Delete the associated RecurrenceRule
        super().delete(*args, **kwargs)
        recurrence_set.save(recalculate=True)


