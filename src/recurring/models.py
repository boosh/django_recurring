import uuid
from datetime import datetime

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
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _
from icalendar import Calendar, Event as ICalEvent

# created in migrations
UTC_ID = 1

MONDAY = "MO"
TUESDAY = "TU"
WEDNESDAY = "WE"
THURSDAY = "TH"
FRIDAY = "FR"
SATURDAY = "SA"
SUNDAY = "SU"


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
        (MO.weekday, MONDAY),
        (TU.weekday, TUESDAY),
        (WE.weekday, WEDNESDAY),
        (TH.weekday, THURSDAY),
        (FR.weekday, FRIDAY),
        (SA.weekday, SATURDAY),
        (SU.weekday, SUNDAY),
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
        null=True,
        blank=True,
        help_text=_("The date and time until which occurrences will be generated"),
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

    def __str__(self):
        return f"RecurrenceRule (Frequency: {self.get_frequency_display()})"

    def get_frequency_display(self):
        return self.Frequency(self.frequency).name

    def get_wkst_display(self):
        return dict(self.WEEKDAYS)[self.wkst] if self.wkst is not None else None

    def clean(self):
        if self.count and self.until:
            raise ValidationError("Only one of either `count` or `until` can be set")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def _get_rrule_kwargs(self, start_date, end_date):
        weekday_map = {
            MONDAY: MO,
            TUESDAY: TU,
            WEDNESDAY: WE,
            THURSDAY: TH,
            FRIDAY: FR,
            SATURDAY: SA,
            SUNDAY: SU,
        }

        kwargs = {
            "freq": self.frequency,
            "interval": self.interval,
            "dtstart": start_date.astimezone(
                pytz.timezone(self.event.calendar_entry.timezone.name)
            ),
            "until": end_date,
        }

        if self.wkst is not None:
            kwargs["wkst"] = weekday_map[self.get_wkst_display()]
        if self.byweekday:
            kwargs["byweekday"] = [weekday_map[day] for day in self.byweekday]
        if self.count is not None:
            kwargs["count"] = self.count
        if self.until is not None:
            kwargs["until"] = self.until
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
            "until": self.until.isoformat() if self.until else None,
            "bysetpos": self.bysetpos,
            "bymonth": self.bymonth,
            "bymonthday": self.bymonthday,
            "byyearday": self.byyearday,
            "byweekno": self.byweekno,
            "byweekday": self.byweekday,
            "byhour": self.byhour,
            "byminute": self.byminute,
            "bysecond": self.bysecond,
            "timezone": self.event.calendar_entry.timezone.name,
        }


class CalendarEntry(models.Model):
    class Meta:
        verbose_name_plural = "Calendar entries"

    name = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text=_("The name of the calendar entry. Will be used as the ical summary"),
    )
    description = models.TextField(
        blank=True, help_text=_("A description of the calendar entry")
    )
    timezone = models.ForeignKey(
        Timezone,
        on_delete=models.SET_DEFAULT,
        default=UTC_ID,
        help_text=_("The timezone for this calendar entry"),
    )
    next_occurrence = models.DateTimeField(
        null=True, blank=True, help_text=_("The next occurrence of this calendar entry")
    )
    previous_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The previous occurrence of this calendar entry"),
    )

    def __str__(self):
        return f"{self.name} (Timezone: {self.timezone.name})"

    def to_rruleset(self):
        rset = rruleset()

        for event in self.events.all():
            rrule_obj = event.recurrence_rule.to_rrule(event.start_time, event.end_time)
            rset.rrule(rrule_obj)

            for exclusion in event.exclusions.all():
                # the time component is kept in sync with the event start time
                rset.exdate(exclusion.get_all_dates())

        return rset

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "timezone": self.timezone.name,
            "events": [
                {
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "is_full_day": event.is_full_day,
                    "rule": event.recurrence_rule.to_dict()
                    if event.recurrence_rule
                    else {},
                    "exclusions": [
                        {
                            "start_date": exclusion.start_date.isoformat(),
                            "end_date": exclusion.end_date.isoformat(),
                        }
                        for exclusion in event.exclusions.all()
                    ],
                }
                for event in self.events.all()
            ],
        }

    def from_dict(self, data):
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.timezone = Timezone.objects.get(
            name=data.get("timezone", self.timezone.name)
        )
        self.save()
        tz = pytz.timezone(self.timezone.name)

        for event_data in data.get("events", []):
            event = Event(
                calendar_entry=self,
                start_time=event_data["start_time"],
                end_time=event_data["end_time"] if event_data.get("end_time") else None,
                is_full_day=event_data["is_full_day"],
            )
            event.save()

            rule_data = event_data.get("recurrence_rule")
            if rule_data:
                rule = RecurrenceRule(
                    frequency=RecurrenceRule.Frequency[rule_data["frequency"]].value,
                    interval=rule_data.get("interval", 1),
                    wkst=rule_data.get("wkst"),
                    count=rule_data.get("count"),
                    until=datetime.fromisoformat(rule_data["until"])
                    if rule_data.get("until")
                    else None,
                    bysetpos=rule_data.get("bysetpos"),
                    bymonth=rule_data.get("bymonth"),
                    bymonthday=rule_data.get("bymonthday"),
                    byyearday=rule_data.get("byyearday"),
                    byweekno=rule_data.get("byweekno"),
                    byweekday=rule_data.get("byweekday"),
                    byhour=rule_data.get("byhour"),
                    byminute=rule_data.get("byminute"),
                    bysecond=rule_data.get("bysecond"),
                )
                rule.save()
                event.recurrence_rule = rule
                event.save()

            for exclusion_data in event_data.get("exclusions", []):
                ExclusionDateRange.objects.create(
                    event=event,
                    start_date=exclusion_data["start_date"].astimezone(tz),
                    end_date=exclusion_data["end_date"].astimezone(tz),
                )

    def recalculate_occurrences(self):
        try:
            rruleset = self.to_rruleset()
            now = django_timezone.now()
            tz = pytz.timezone(self.timezone.name)

            next_occurrence = rruleset.after(now, inc=False)
            self.next_occurrence = (
                next_occurrence.astimezone(tz) if next_occurrence else None
            )

            prev_occurrence = rruleset.before(now, inc=False)
            self.previous_occurrence = (
                prev_occurrence.astimezone(tz) if prev_occurrence else None
            )
        except Exception as e:
            print(
                f"Error recalculating occurrences for CalendarEntry {self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        recalculate = kwargs.pop("recalculate", True)
        super().save(*args, **kwargs)
        if recalculate:
            self.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        # todo - is this required? everything is on delete cascade
        for event in self.events.all():
            event.recurrence_rule.delete()
            event.delete()
        super().delete(*args, **kwargs)

    def to_ical(self, prod_id: str = None) -> str:
        """
        Convert the CalendarEntry to an iCal string representation.

        Args:
            prod_id (str, optional): The PRODID to use in the iCal. Defaults to None.

        Returns:
            str: The iCal string representation of the calendar entry.
        """
        cal = Calendar()
        cal.add("version", "2.0")

        if prod_id is None:
            prod_id = getattr(
                settings, "ICAL_PROD_ID", "-//django-recurring//NONSGML v1.0//EN"
            )
        cal.add("prodid", prod_id)

        if not self.events.exists():
            return ""

        for event in self.events.all():
            ical_event = ICalEvent()
            ical_event.add("dtstamp", django_timezone.now())
            ical_event.add("uid", str(uuid.uuid4()))
            ical_event.add("summary", self.name)
            ical_event.add("dtstart", event.start_time)
            if event.end_time:
                ical_event.add("dtend", event.end_time)

            rule = event.recurrence_rule
            if rule:
                rrule_dict = {
                    "freq": rule.get_frequency_display(),
                    "interval": rule.interval,
                }
                if rule.wkst is not None:
                    rrule_dict["wkst"] = rule.wkst
                if rule.count is not None:
                    rrule_dict["count"] = rule.count
                if rule.until is not None:
                    rrule_dict["until"] = rule.until
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

                ical_event.add("rrule", rrule_dict)

            # the time component is kept in sync with the event start time
            exdates = [
                date
                for exclusion in event.exclusions.all()
                for date in exclusion.get_all_dates()
            ]
            if exdates:
                ical_event.add("exdate", exdates)

            cal.add_component(ical_event)

        return cal.to_ical().decode("utf-8")


class Event(models.Model):
    calendar_entry = models.ForeignKey(
        CalendarEntry, on_delete=models.CASCADE, related_name="events"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_full_day = models.BooleanField(default=False)
    recurrence_rule = models.OneToOneField(
        RecurrenceRule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("The recurrence rule"),
    )

    def clean(self):
        if not self.is_full_day and self.end_time is None:
            raise ValidationError("End time is required for non-full day events.")
        if self.is_full_day and self.end_time:
            raise ValidationError("End time should not be set for full day events.")
        if not self.is_full_day and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                "Start time must be before end time for non-full day events."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.update_exclusions()

    def update_exclusions(self):
        for exclusion in self.exclusions.all():
            exclusion.sync_time_component()
            exclusion.save(sync_time=False)

    def __str__(self):
        return f"Event for {self.calendar_entry.name}: {self.start_time}"


class ExclusionDateRange(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="exclusions",
        help_text=_("The event this exclusion date range belongs to"),
    )
    start_date = models.DateTimeField(
        help_text=_("The start date of the exclusion range")
    )
    end_date = models.DateTimeField(help_text=_("The end date of the exclusion range"))

    def __str__(self):
        return f"Exclusion date range for {self.event}: {self.start_date} to {self.end_date}"

    def clean(self):
        super().clean()
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be less than the end date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        sync_time = kwargs.pop("sync_time", True)
        if sync_time:
            self.sync_time_component()
        super().save(*args, **kwargs)
        self.event.calendar_entry.recalculate_occurrences()

    def delete(self, *args, **kwargs):
        calendar_entry = self.event.calendar_entry
        super().delete(*args, **kwargs)
        calendar_entry.recalculate_occurrences()

    def sync_time_component(self):
        event_time = self.event.start_time.time()
        self.start_date = datetime.combine(self.start_date.date(), event_time)
        self.end_date = datetime.combine(self.end_date.date(), event_time)

    def to_rrule(self):
        kwargs = {
            "dtstart": self.start_date.astimezone(
                pytz.timezone(self.event.calendar_entry.timezone.name)
            ),
            "until": self.end_date,
        }
        return rrule(**kwargs)

    def get_all_dates(self) -> list[datetime]:
        return list(rrule(DAILY, dtstart=self.start_date, until=self.end_date))
