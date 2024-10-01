import uuid
from datetime import timedelta

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
from django.conf import settings
from django.db import models
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _
from icalendar import Calendar, Event

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
    bysetpos = models.JSONField(
        null=True, blank=True, help_text=_("By position (BYSETPOS)")
    )
    bymonth = models.JSONField(null=True, blank=True, help_text=_("By month (BYMONTH)"))
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
    byhour = models.JSONField(null=True, blank=True, help_text=_("By hour (BYHOUR)"))
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

    def _get_rrule_kwargs(self, start_date, end_date):
        weekday_map = {
            "MO": MO,
            "TU": TU,
            "WE": WE,
            "TH": TH,
            "FR": FR,
            "SA": SA,
            "SU": SU,
        }

        kwargs = {
            "freq": self.frequency,
            "interval": self.interval,
            "dtstart": start_date.astimezone(pytz.timezone(self.timezone.name)),
            "until": end_date,
        }

        if self.wkst is not None:
            kwargs["wkst"] = weekday_map[self.wkst]
        if self.count is not None:
            kwargs["count"] = self.count
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

        return kwargs

    def to_rrule(self, start_date, end_date):
        return rrule(**self._get_rrule_kwargs(start_date, end_date))

    def to_dict(self):
        return {
            "id": self.id,
            "frequency": self.Frequency(self.frequency).name,
            "interval": self.interval,
            "wkst": self.wkst,
            "count": self.count,
            "bysetpos": self.bysetpos,
            "bymonth": self.bymonth,
            "bymonthday": self.bymonthday,
            "byyearday": self.byyearday,
            "byweekno": self.byweekno,
            "byweekday": self.byweekday,
            "byhour": self.byhour,
            "byminute": self.byminute,
            "bysecond": self.bysecond,
            "timezone": self.timezone.name,
        }


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
        recurrence_set_rule = RecurrenceSetRule.objects.filter(
            recurrence_rule=self.recurrence_rule
        ).first()
        if recurrence_set_rule:
            recurrence_set_rule.recurrence_set.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        recurrence_set_rule = RecurrenceSetRule.objects.filter(
            recurrence_rule=self.recurrence_rule
        ).first()
        super().delete(*args, **kwargs)
        if recurrence_set_rule:
            recurrence_set_rule.recurrence_set.recalculate_occurrences()


class RecurrenceSet(models.Model):
    name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text=_("The name of the recurrence set"),
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

        for rule in self.recurrencesetrules.all():
            for date_range in rule.recurrence_rule.date_ranges.all():
                rrule_obj = rule.recurrence_rule.to_rrule(
                    date_range.start_date, date_range.end_date
                )
                if date_range.is_exclusion:
                    rset.exrule(rrule_obj)
                else:
                    rset.rrule(rrule_obj)

        return rset

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "timezone": self.timezone.name,
            "rules": [
                {
                    "is_exclusion": rule.is_exclusion,
                    "rule": rule.recurrence_rule.to_dict(),
                    "date_ranges": [
                        {
                            "start_date": date_range.start_date.isoformat(),
                            "end_date": date_range.end_date.isoformat(),
                            "is_exclusion": date_range.is_exclusion,
                        }
                        for date_range in rule.recurrence_rule.date_ranges.all()
                    ],
                }
                for rule in self.recurrencesetrules.all()
            ],
        }

    def from_dict(self, data):
        rules = []
        for rule_data in data.get("rules", []):
            rule = RecurrenceRule()
            rule_dict = rule_data["rule"]
            rule.frequency = RecurrenceRule.Frequency[rule_dict["frequency"]].value
            rule.interval = rule_dict.get("interval", 1)
            rule.wkst = rule_dict.get("wkst")
            rule.count = rule_dict.get("count")
            rule.timezone = self.timezone

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
                value = rule_dict.get(field)
                if value is not None:
                    setattr(rule, field, value)

            date_ranges = []
            for date_range_data in rule_data.get("date_ranges", []):
                date_ranges.append(
                    RecurrenceRuleDateRange(
                        start_date=date_range_data["start_date"],
                        end_date=date_range_data["end_date"],
                        is_exclusion=date_range_data.get("is_exclusion", False),
                    )
                )

            rules.append(
                {
                    "rule": rule,
                    "is_exclusion": rule_data.get("is_exclusion", False),
                    "date_ranges": date_ranges,
                }
            )

        for rule_data in rules:
            rule = rule_data["rule"]
            rule.save()
            RecurrenceSetRule.objects.create(
                recurrence_set=self,
                recurrence_rule=rule,
                is_exclusion=rule_data["is_exclusion"],
            )
            for date_range in rule_data["date_ranges"]:
                date_range.recurrence_rule = rule
                date_range.save()

    def recalculate_occurrences(self):
        try:
            rruleset = self.to_rruleset()
            now = django_timezone.now()
            tz = pytz.timezone(self.timezone.name)

            # Calculate next occurrence
            next_occurrence = rruleset.after(now, inc=False)
            self.next_occurrence = (
                next_occurrence.astimezone(tz) if next_occurrence else None
            )

            # Calculate previous occurrence
            prev_occurrence = rruleset.before(now, inc=False)
            self.previous_occurrence = (
                prev_occurrence.astimezone(tz) if prev_occurrence else None
            )
        except Exception as e:
            print(
                f"Error recalculating occurrences for RecurrenceSet {self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        recalculate = kwargs.pop("recalculate", True)
        super().save(*args, **kwargs)
        if recalculate:
            self.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        # Delete related RecurrenceRules and RecurrenceRuleDateRanges
        for rule in self.recurrencesetrules.all():
            rule.recurrence_rule.date_ranges.all().delete()
            rule.recurrence_rule.delete()
        super().delete(*args, **kwargs)

    def to_ical(self, prod_id: str = None) -> str:
        """
        Convert the RecurrenceSet to an iCal string representation.

        Args:
            prod_id (str, optional): The PRODID to use in the iCal. Defaults to None.

        Returns:
            str: The iCal string representation of the recurrence set.
        """
        cal = Calendar()
        cal.add("version", "2.0")

        # Set PRODID
        if prod_id is None:
            prod_id = getattr(
                settings, "ICAL_PROD_ID", "-//django-recurring//NONSGML v1.0//EN"
            )
        cal.add("prodid", prod_id)

        if not self.recurrencesetrules.exists():
            return ""  # Return empty string if no rules

        for recurrence_set_rule in self.recurrencesetrules.all():
            rule = recurrence_set_rule.recurrence_rule

            rule_date_ranges = rule.date_ranges.all()
            earliest_start = min(dr.start_date for dr in rule_date_ranges)
            latest_end = max(dr.end_date for dr in rule_date_ranges)

            event = Event()
            event.add("dtstamp", django_timezone.now())
            event.add("uid", str(uuid.uuid4()))
            event.add("dtstart", earliest_start)
            event.add("dtend", latest_end)

            rrule_dict = {
                "freq": rule.get_frequency_display(),
                "interval": rule.interval,
                "until": latest_end,
            }
            if rule.wkst is not None:
                rrule_dict["wkst"] = rule.wkst
            if rule.count is not None:
                rrule_dict["count"] = rule.count
            if rule.bysetpos:
                rrule_dict["bysetpos"] = rule.bysetpos
            if rule.bymonth:
                rrule_dict["bymonth"] = rule.bymonth
            if rule.bymonthday:
                rrule_dict["bymonthday"] = rule.bymonthday
            if rule.byyearday:
                rrule_dict["byyearday"] = rule.byyearday
            if rule.byweekno:
                rrule_dict["byweekno"] = rule.byweekno
            if rule.byweekday:
                rrule_dict["byday"] = rule.byweekday
            if rule.byhour:
                rrule_dict["byhour"] = rule.byhour
            if rule.byminute:
                rrule_dict["byminute"] = rule.byminute
            if rule.bysecond:
                rrule_dict["bysecond"] = rule.bysecond

            exdates = []

            for date_range in rule_date_ranges:
                if date_range.is_exclusion:
                    current_date = date_range.start_date
                    range_exdates = []

                    while current_date <= date_range.end_date:
                        range_exdates.append(current_date)
                        current_date += timedelta(days=1)

                    exdates.extend(range_exdates)

            if exdates:
                event.add("exdate", exdates)
            event.add("rrule", rrule_dict)

            cal.add_component(event)

        return cal.to_ical().decode("utf-8")


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
    # todo - I think we can get rid of this
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
