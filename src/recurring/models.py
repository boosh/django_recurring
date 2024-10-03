import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

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
    """
    Represents a timezone in the system.

    :param name: The name of the timezone
    :type name: str
    """

    name = models.CharField(
        max_length=64, unique=True, help_text=_("The name of the timezone")
    )

    @property
    def as_tz(self):
        """
        Returns the timezone as a pytz timezone object.

        :return: A pytz timezone object
        :rtype: pytz.timezone
        """
        return pytz.timezone(self.name)

    def __str__(self) -> str:
        """
        Returns a string representation of the Timezone object.

        :return: The name of the timezone
        :rtype: str
        """
        return self.name


class RecurrenceRule(models.Model):
    """
    Represents a recurrence rule for calendar events.

    This model defines the parameters for recurring events, including frequency,
    interval, and various constraints on recurrence.
    """

    class Frequency(models.IntegerChoices):
        """
        Enumeration of possible frequency values for recurrence.
        """

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

    def __str__(self) -> str:
        """
        Returns a string representation of the RecurrenceRule.

        :return: A string describing the RecurrenceRule
        :rtype: str
        """
        return f"RecurrenceRule (Frequency: {self.get_frequency_display()})"

    def get_frequency_display(self) -> str:
        """
        Returns the display name of the frequency.

        :return: The name of the frequency
        :rtype: str
        """
        return self.Frequency(self.frequency).name

    def get_wkst_display(self) -> Optional[str]:
        """
        Returns the display name of the week start day.

        :return: The name of the week start day, or None if not set
        :rtype: Optional[str]
        """
        return dict(self.WEEKDAYS)[self.wkst] if self.wkst is not None else None

    def clean(self) -> None:
        """
        Validates the RecurrenceRule object.

        :raises ValidationError: If both count and until are set
        """
        if self.count and self.until:
            raise ValidationError("Only one of either `count` or `until` can be set")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the RecurrenceRule object after full cleaning.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def _get_rrule_kwargs(self, start_date: datetime) -> Dict[str, Any]:
        """
        Generates keyword arguments for creating an rrule object.

        :param start_date: The start date for the recurrence rule
        :type start_date: datetime
        :return: A dictionary of keyword arguments for rrule
        :rtype: Dict[str, Any]
        """
        weekday_map = {
            MONDAY: MO,
            TUESDAY: TU,
            WEDNESDAY: WE,
            THURSDAY: TH,
            FRIDAY: FR,
            SATURDAY: SA,
            SUNDAY: SU,
        }

        kwargs: Dict[str, Any] = {
            "freq": self.frequency,
            "interval": self.interval,
            "dtstart": start_date.astimezone(self.event.calendar_entry.timezone.as_tz),
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

    def to_rrule(self, start_date: datetime) -> rrule:
        """
        Creates an rrule object from the RecurrenceRule.

        :param start_date: The start date for the recurrence rule
        :type start_date: datetime
        :return: An rrule object
        :rtype: rrule
        """
        return rrule(**self._get_rrule_kwargs(start_date))

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the RecurrenceRule to a dictionary representation.

        :return: A dictionary representation of the RecurrenceRule
        :rtype: Dict[str, Any]
        """
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
            "timezone": self.event.calendar_entry.timezone.name
            if hasattr(self, "event")
            else None,
        }


class CalendarEntry(models.Model):
    """
    Represents a calendar entry with associated events and recurrence rules.
    """

    class Meta:
        verbose_name_plural = "Calendar entries"

    name = models.CharField(
        max_length=255,
        help_text=_(
            "The name of the calendar entry. Will be used as the ical filename, slugified, and ical summary if no description is set"
        ),
    )
    description = models.TextField(
        blank=True,
        help_text=_(
            "A description of the calendar entry. Will be used as the ical summary"
        ),
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
        """
        Returns a string representation of the CalendarEntry.

        :return: A string describing the CalendarEntry
        :rtype: str
        """
        return f"{self.name} (Timezone: {self.timezone.name})"

    def to_rruleset(self):
        """
        Converts the CalendarEntry to an rruleset object.

        :return: An rruleset object representing the CalendarEntry
        :rtype: rruleset
        """
        rset = rruleset()

        for event in self.events.all():
            if event.recurrence_rule:
                rrule_obj = event.recurrence_rule.to_rrule(event.start_time)
                rset.rrule(rrule_obj)
            else:
                # If there's no recurrence rule, add the event as a single occurrence
                rset.rdate(event.start_time)

            for exclusion in event.exclusions.all():
                # the time component is kept in sync with the event start time
                for exclusion_date in exclusion.get_all_dates():
                    rset.exdate(exclusion_date)

        return rset

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the CalendarEntry to a dictionary representation.

        :return: A dictionary representation of the CalendarEntry
        :rtype: Dict[str, Any]
        """
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

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Populates the CalendarEntry from a dictionary representation.

        :param data: A dictionary containing CalendarEntry data
        :type data: Dict[str, Any]
        """
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.timezone = Timezone.objects.get(
            name=data.get("timezone", self.timezone.name)
        )
        self.save(recalculate=False)
        tz = self.timezone.as_tz

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

    def recalculate_occurrences(self) -> None:
        """
        Recalculates the next and previous occurrences of the CalendarEntry.
        """
        try:
            rruleset = self.to_rruleset()
            now = django_timezone.now()
            tz = self.timezone.as_tz

            # Find the next occurrence
            self.next_occurrence = rruleset.after(now)
            if self.next_occurrence:
                self.next_occurrence = self.next_occurrence.astimezone(tz)

            # Find the previous occurrence
            self.previous_occurrence = rruleset.before(now, inc=False)
            if self.previous_occurrence:
                self.previous_occurrence = self.previous_occurrence.astimezone(tz)

        except Exception as e:
            print(
                f"Error recalculating occurrences for CalendarEntry {self.id}: {str(e)}"
            )
            traceback.print_exc()

            # Set occurrences to None if there's an error
            self.next_occurrence = None
            self.previous_occurrence = None

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the CalendarEntry and optionally recalculates occurrences.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        recalculate = kwargs.pop("recalculate", True)
        super().save(*args, **kwargs)
        if recalculate:
            self.recalculate_occurrences()

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Deletes the CalendarEntry and associated events and recurrence rules.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        # todo - is this required? everything is on delete cascade
        for event in self.events.all():
            event.recurrence_rule.delete()
            event.delete()
        super().delete(*args, **kwargs)

    def to_ical(self, prod_id: Optional[str] = None) -> str:
        """
        Convert the CalendarEntry to an iCal string representation.

        :param prod_id: The PRODID to use in the iCal. Defaults to None.
        :type prod_id: Optional[str]
        :return: The iCal string representation of the calendar entry.
        :rtype: str
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
            ical_event.add(
                "summary", self.description if self.description else self.name
            )
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
    """
    Represents an event within a CalendarEntry.
    """

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

    def clean(self) -> None:
        """
        Validates the Event object.

        :raises ValidationError: If the event data is invalid
        """
        if not self.is_full_day and self.end_time is None:
            raise ValidationError("End time is required for non-full day events.")
        if self.is_full_day and self.end_time:
            raise ValidationError("End time should not be set for full day events.")
        if not self.is_full_day and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                "Start time must be before end time for non-full day events."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the Event object after full cleaning and updates exclusions.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)
        self.update_exclusions()

    def update_exclusions(self) -> None:
        """
        Updates the time component of all exclusions associated with this event.
        """
        for exclusion in self.exclusions.all():
            exclusion.sync_time_component()
            exclusion.save(sync_time=False)

    def __str__(self) -> str:
        """
        Returns a string representation of the Event.

        :return: A string describing the Event
        :rtype: str
        """
        return f"Event for {self.calendar_entry.name}: {self.start_time}"


class ExclusionDateRange(models.Model):
    """
    Represents a date range for which an event should be excluded from recurrence.
    """

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

    def __str__(self) -> str:
        """
        Returns a string representation of the ExclusionDateRange.

        :return: A string describing the ExclusionDateRange
        :rtype: str
        """
        return f"Exclusion date range for {self.event}: {self.start_date} to {self.end_date}"

    def clean(self) -> None:
        """
        Validates the ExclusionDateRange object.

        :raises ValidationError: If the start date is not less than the end date
        """
        super().clean()
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be less than the end date.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the ExclusionDateRange object after full cleaning and optionally syncs time component.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        self.full_clean()
        sync_time = kwargs.pop("sync_time", True)
        if sync_time:
            self.sync_time_component()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Deletes the ExclusionDateRange object and recalculates occurrences for the associated CalendarEntry.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        calendar_entry = self.event.calendar_entry
        super().delete(*args, **kwargs)
        calendar_entry.recalculate_occurrences()

    def sync_time_component(self) -> None:
        """
        Synchronizes the time component of the start and end dates with the event's start time.
        """
        event_time = self.event.start_time.time()
        tz = self.event.calendar_entry.timezone.as_tz
        self.start_date = tz.localize(
            datetime.combine(self.start_date.date(), event_time)
        )
        self.end_date = tz.localize(datetime.combine(self.end_date.date(), event_time))

    def to_rrule(self) -> rrule:
        """
        Converts the ExclusionDateRange to an rrule object.

        :return: An rrule object representing the ExclusionDateRange
        :rtype: rrule
        """
        kwargs = {
            "dtstart": self.start_date.astimezone(
                self.event.calendar_entry.timezone.as_tz
            ),
            "until": self.end_date.astimezone(self.event.calendar_entry.timezone.as_tz),
        }
        return rrule(**kwargs)

    def get_all_dates(self) -> list[datetime]:
        """
        Returns a list of all dates within the ExclusionDateRange.

        :return: A list of datetime objects
        :rtype: list[datetime]
        """
        return list(rrule(DAILY, dtstart=self.start_date, until=self.end_date))
