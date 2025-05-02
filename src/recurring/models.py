import logging
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
from django.template.defaultfilters import date as date_filter
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _
from icalendar import Calendar, Event as ICalEvent

# created in migrations
UTC_ID = 1


class WeekDay:
    MONDAY = repr(MO)  # e.g. 'MO', etc.
    TUESDAY = repr(TU)
    WEDNESDAY = repr(WE)
    THURSDAY = repr(TH)
    FRIDAY = repr(FR)
    SATURDAY = repr(SA)
    SUNDAY = repr(SU)


logger = logging.getLogger(__name__)


class Timezone(models.Model):
    """
    Represents a timezone in the system.

    This is just an optimisation to denormalise data. You'll probably
    want your own Timezone model with extra fields that you actually
    display to users (if you let them select timezones, etc).

    :param name: The name of the timezone
    :type name: str
    """

    name = models.CharField(
        max_length=64, unique=True, help_text=_("The name of the timezone")
    )

    @property
    def as_tz(self):
        """
        Returns the timezone as a ZoneInfo timezone object.

        :return: A ZoneInfo timezone object
        :rtype: ZoneInfo
        """
        return ZoneInfo(self.name)

    def __str__(self) -> str:
        """
        Returns a string representation of the Timezone object.

        :return: The name of the timezone
        :rtype: str
        """
        return self.name

    def clean(self) -> None:
        try:
            ZoneInfo(self.name)
        except ZoneInfoNotFoundError:
            raise ValidationError(f"Invalid timezone: {self.name}")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the TimeZone object after full cleaning.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        self.full_clean()
        super().save(*args, **kwargs)


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
        (MO.weekday, WeekDay.MONDAY),
        (TU.weekday, WeekDay.TUESDAY),
        (WE.weekday, WeekDay.WEDNESDAY),
        (TH.weekday, WeekDay.THURSDAY),
        (FR.weekday, WeekDay.FRIDAY),
        (SA.weekday, WeekDay.SATURDAY),
        (SU.weekday, WeekDay.SUNDAY),
    )

    frequency = models.IntegerField(
        choices=Frequency.choices, help_text=_("The frequency of the recurrence")
    )

    @property
    def frequency_name(self):
        return RecurrenceRule.Frequency(self.frequency).name.lower()

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
            WeekDay.MONDAY: MO,
            WeekDay.TUESDAY: TU,
            WeekDay.WEDNESDAY: WE,
            WeekDay.THURSDAY: TH,
            WeekDay.FRIDAY: FR,
            WeekDay.SATURDAY: SA,
            WeekDay.SUNDAY: SU,
        }

        timezone = (
            self.event.calendar_entry.timezone.as_tz if hasattr(self, "event") else None
        )

        kwargs: Dict[str, Any] = {
            "freq": self.frequency,
            "interval": self.interval,
            "dtstart": start_date.astimezone(timezone) if timezone else start_date,
        }

        if self.wkst is not None:
            kwargs["wkst"] = weekday_map[self.get_wkst_display()]
        if self.byweekday:
            kwargs["byweekday"] = [weekday_map[day] for day in self.byweekday]
        if self.count is not None:
            kwargs["count"] = self.count
        if self.until and timezone:
            kwargs["until"] = self.until.astimezone(timezone)
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
            # todo - remove this since it's already on the calendar entry
            "timezone": self.event.calendar_entry.timezone.name
            if hasattr(self, "event")
            else None,
        }


WEEKDAY_ABBR = {
    "MO": "Mon",
    "TU": "Tue",
    "WE": "Wed",
    "TH": "Thu",
    "FR": "Fri",
    "SA": "Sat",
    "SU": "Sun",
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
            "Will be used as the ical filename, slugified, and ical summary if no description is set"
        ),
    )
    description = models.TextField(
        blank=True,
        help_text=_("Will be used as the ical summary"),
    )
    timezone = models.ForeignKey(
        Timezone,
        on_delete=models.SET_DEFAULT,
        default=UTC_ID,
        help_text=_("The timezone for this calendar entry"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The first occurrence of this calendar entry"),
    )
    last_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The last occurrence of this calendar entry"),
    )
    next_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "The next occurrence of this calendar entry from the last time occurrences were calculated"
        ),
    )
    previous_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "The previous occurrence of this calendar entry from the last time occurrences were calculated"
        ),
    )

    def __str__(self, format_template=None):
        """
        Returns a human-readable description of when this calendar entry occurs.
        The format can be customized via the format_template parameter or the CALENDAR_ENTRY_FORMAT setting.

        Default format is like: "Every Mon, Wed, Fri at 12:00 (Europe/London) from today until 31 Dec 24"

        :param format_template: Optional string template with {name} and {occurrences} placeholders
        :type format_template: Optional[str]
        :return: A string describing when the calendar entry occurs
        :rtype: str
        """
        # Allow custom formatting via parameter or settings
        if format_template is None:
            format_template = getattr(
                settings, "CALENDAR_ENTRY_FORMAT", "{name}: {occurrences}"
            )

        if not self.events.exists():
            return format_template.format(name=self.name, occurrences="No events")

        def format_datetime(dt):
            if not dt:
                return "forever"
            return date_filter(dt, "j M y")

        def format_time(dt):
            if not dt:
                return ""
            return date_filter(dt, "H:i")

        parts = []
        for event in self.events.all():
            event_str = []

            if event.recurrence_rule:
                rule = event.recurrence_rule
                freq_name = rule.frequency_name.lower()

                if freq_name == "daily":
                    event_str.append("Every day")
                elif freq_name == "weekly":
                    if rule.byweekday:
                        weekdays = [
                            WEEKDAY_ABBR[day.split("[")[0]] for day in rule.byweekday
                        ]
                        event_str.append(f"Every {', '.join(weekdays)}")
                    else:
                        event_str.append("Every week")
                elif freq_name == "monthly":
                    if rule.bymonthday:
                        days = [str(d) for d in rule.bymonthday]
                        event_str.append(f"Every month on the {', '.join(days)}")
                    else:
                        event_str.append("Every month")
                elif freq_name == "yearly":
                    event_str.append("Every year")

                if rule.interval > 1:
                    event_str[-1] = event_str[-1].replace(
                        "Every", f"Every {rule.interval}"
                    )
            else:
                event_str.append("Once")

            if not event.is_full_day:
                event_str.append(f"at {format_time(event.start_time)}")
                if event.end_time:
                    event_str[-1] += f"-{format_time(event.end_time)}"

            event_str.append(f"({self.timezone.name})")

            if event.recurrence_rule:
                rule = event.recurrence_rule
                if rule.until:
                    event_str.append(f"until {format_datetime(rule.until)}")
                elif rule.count:
                    event_str.append(f"for {rule.count} occurrences")

            parts.append(" ".join(event_str))

        return format_template.format(name=self.name, occurrences=", then ".join(parts))

    def to_rruleset(self):
        """
        Converts the CalendarEntry to an rruleset object.

        :return: An rruleset object representing the CalendarEntry
        :rtype: rruleset
        """
        rset = rruleset()

        for event in self.events.all():
            # add the event as a single event in case it isn't
            # included in any recurrence rules
            rset.rdate(event.start_time)

            if event.recurrence_rule:
                rrule_obj = event.recurrence_rule.to_rrule(event.start_time)
                rset.rrule(rrule_obj)

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
                    "recurrence_rule": event.recurrence_rule.to_dict()
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
                    until=rule_data["until"] if rule_data.get("until") else None,
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
                    start_date=exclusion_data["start_date"],
                    end_date=exclusion_data["end_date"],
                )

    def calculate_occurrences(
        self, window_days: int = 365, window_multiple: int = 3
    ) -> None:
        """
        Recalculates the cached occurrences of the CalendarEntry in **UTC**. Calculated occurrences include:

        * first_occurrence/last_occurrence (across all events in the CalendarEntry). Capped based on the window parameters for performance reasons.
        * previous_occurrence/next_occurrence (relative to the time this method was last called)

        :param window_days: The number of days to use as the basis for calculating the delta from now for the 'first'/'last' occurrences
        :param window_multiple: Multiplied by `occurence_window_days` to create the delta from now to use to calculate the 'first'/'last' occurrences. E.g. if window_days=365 and window_multiple=5, we'll only look forwards and backwards 5 years to calculate the 'first' and 'last' occurrences.
        """
        try:
            rruleset = self.to_rruleset()
            utc = ZoneInfo("UTC")
            tz = self.timezone.as_tz
            now = datetime.now().astimezone(tz)

            def adjust_for_dst(dt):
                if dt is None:
                    return None
                updated_at_dst = self.updated_at.astimezone(tz).dst()
                current_dst = now.dst()

                if current_dst < updated_at_dst:
                    return (dt - current_dst).astimezone(utc)
                else:
                    return dt.astimezone(utc)

            next_occurrence_dt = rruleset.after(now)
            self.next_occurrence = adjust_for_dst(next_occurrence_dt)

            previous_occurrence_dt = rruleset.before(now, inc=False)
            self.previous_occurrence = adjust_for_dst(previous_occurrence_dt)

            window_delta = timedelta(days=window_days * window_multiple)

            first_occurrence_dt = rruleset.after(now - window_delta, inc=True)
            self.first_occurrence = adjust_for_dst(first_occurrence_dt)

            last_occurrence_dt = rruleset.before(now + window_delta, inc=True)
            self.last_occurrence = adjust_for_dst(last_occurrence_dt)
        except Exception as e:
            print(
                f"Error recalculating occurrences for CalendarEntry {self.id}: {str(e)}"
            )
            traceback.print_exc()

        self.save(recalculate=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the CalendarEntry and optionally recalculates occurrences.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        :keyword bool recalculate: Whether to recalculate occurrences. Defaults to ``True``.
        """
        recalculate = kwargs.pop("recalculate", True)
        super().save(*args, **kwargs)
        if recalculate:
            self.calculate_occurrences()

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Deletes the CalendarEntry and associated events and recurrence rules.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        for event in self.events.all():
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
        tz = self.timezone.as_tz

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
            ical_event.add("dtstart", event.start_time.astimezone(tz))
            if event.end_time:
                ical_event.add("dtend", event.end_time.astimezone(tz))

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
                    rrule_dict["until"] = rule.until.astimezone(tz)
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

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Deletes all associated recurrence rules.

        :param args: Variable length argument list
        :param kwargs: Arbitrary keyword arguments
        """
        if self.recurrence_rule:
            logger.info("Deleting event recurrence rules")
            self.recurrence_rule.delete()
        return super().delete(*args, **kwargs)


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
        calendar_entry.calculate_occurrences()

    def sync_time_component(self) -> None:
        """
        Synchronizes the time component of the start and end dates with the event's start time.
        """
        event_time = self.event.start_time.time()
        tz = self.event.calendar_entry.timezone.as_tz
        self.start_date = datetime.combine(
            self.start_date.date(), event_time, tzinfo=tz
        )
        self.end_date = datetime.combine(self.end_date.date(), event_time, tzinfo=tz)

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
        if not hasattr(self.event, "recurrence_rule") or not self.event.recurrence_rule:
            return []

        tz = self.event.calendar_entry.timezone.as_tz
        return list(
            rrule(
                self.event.recurrence_rule.frequency,
                dtstart=self.start_date.astimezone(tz),
                until=self.end_date.astimezone(tz),
            )
        )
