import json
import logging
from datetime import datetime
from typing import Any, Dict

from django import forms

from .models import CalendarEntry
from .widgets import CalendarEntryWidget

logger = logging.getLogger(__name__)


class CalendarEntryForm(forms.ModelForm):
    calendar_entry = forms.CharField(required=False, widget=CalendarEntryWidget)

    class Meta:
        model = CalendarEntry
        fields = ["name", "description", "timezone"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        logger.info("Form init method")
        self.fields["calendar_entry"].widget = CalendarEntryWidget(form=self)
        self.fields["calendar_entry"].widget.attrs["style"] = "display: none;"

        if self.instance.pk:
            calendar_entry_data = self.instance.to_dict()
            self.initial["calendar_entry"] = json.dumps(calendar_entry_data)
            self.fields["calendar_entry"].widget.attrs["data-initial"] = json.dumps(
                calendar_entry_data
            )

    def save(self, commit: bool = True) -> CalendarEntry:
        logger.info(f"Starting save method (commit={commit})")
        instance = super().save(commit=False)
        if commit:
            logger.info("Commit is True, saving instance")
            instance.save(recalculate=False)  # Save without recalculating

            logger.info("Processing calendar_entry data")
            calendar_entry_data = self.cleaned_data.get("calendar_entry")
            if calendar_entry_data:
                logger.info("Clearing existing events")
                for event in instance.events.all():
                    event.delete()

                logger.info("Adding new events and exclusions")
                instance.from_dict(calendar_entry_data)
                instance.save(recalculate=False)

            logger.info("Recalculating occurrences")
            instance.calculate_occurrences()

        logger.info("Save method completed")
        return instance

    def clean(self) -> Dict[str, Any]:
        logger.info("Inside clean")
        cleaned_data = super().clean()

        if self.errors:
            logger.info("Returning errors")
            return cleaned_data

        logger.info("No form errors")
        calendar_entry_data = cleaned_data.get("calendar_entry")
        if calendar_entry_data:
            try:
                calendar_entry_dict = json.loads(calendar_entry_data)

                if not isinstance(calendar_entry_dict, dict):
                    raise ValueError("Calendar entry data must be a dictionary")

                self.calendar_entry_data = calendar_entry_dict

                if not isinstance(calendar_entry_dict.get("events"), list):
                    raise ValueError(
                        "Calendar entry data must contain an 'events' list"
                    )

                # Get the submitted timezone
                submitted_timezone = cleaned_data.get("timezone").as_tz

                for event_data in calendar_entry_dict["events"]:
                    if not isinstance(event_data, dict):
                        raise ValueError("Each event must be a dictionary")
                    if "start_time" not in event_data or "end_time" not in event_data:
                        raise ValueError(
                            "Each event must have 'start_time' and 'end_time'"
                        )

                    # Convert start_time and end_time to timezone-aware datetimes
                    start_time = datetime.fromisoformat(event_data["start_time"])
                    end_time = (
                        datetime.fromisoformat(event_data["end_time"])
                        if event_data["end_time"]
                        else None
                    )

                    # Ensure the datetimes are timezone-aware
                    event_data["start_time"] = start_time.replace(
                        tzinfo=submitted_timezone
                    )

                    event_data["end_time"] = (
                        end_time.replace(tzinfo=submitted_timezone)
                        if end_time
                        else None
                    )
                    event_data["is_full_day"] = event_data.get("is_full_day", False)

                    # Rule and exclusions are optional
                    if "recurrence_rule" in event_data:
                        if not event_data["recurrence_rule"]:
                            event_data["recurrence_rule"] = {}
                        if not isinstance(event_data["recurrence_rule"], dict):
                            raise ValueError("Event rule must be a dictionary")

                        recurrence_rule = event_data["recurrence_rule"]
                        if "until" in recurrence_rule:
                            until = datetime.fromisoformat(recurrence_rule["until"])
                            recurrence_rule["until"] = until.replace(
                                tzinfo=submitted_timezone
                            )

                    if "exclusions" in event_data:
                        if not isinstance(event_data["exclusions"], list):
                            raise ValueError("Event exclusions must be a list")

                        for exclusion_data in event_data["exclusions"]:
                            if not isinstance(exclusion_data, dict):
                                raise ValueError("Each exclusion must be a dictionary")
                            if (
                                "start_date" not in exclusion_data
                                or "end_date" not in exclusion_data
                            ):
                                raise ValueError(
                                    "Each exclusion must have 'start_date' and 'end_date'"
                                )

                            exclusion_start = datetime.fromisoformat(
                                exclusion_data["start_date"]
                            )
                            exclusion_end = datetime.fromisoformat(
                                exclusion_data["end_date"]
                            )

                            exclusion_data["start_date"] = exclusion_start.replace(
                                tzinfo=submitted_timezone
                            )

                            exclusion_data["end_date"] = exclusion_end.replace(
                                tzinfo=submitted_timezone
                            )

                            # Assert that start_date <= end_date
                            if (
                                exclusion_data["start_date"]
                                >= exclusion_data["end_date"]
                            ):
                                raise ValueError(
                                    "Exclusion start date must be less than the end date."
                                )

            except json.JSONDecodeError:
                self.add_error(
                    "calendar_entry", "Invalid JSON data for calendar entry."
                )
            except KeyError as e:
                self.add_error(
                    "calendar_entry",
                    f"Missing required key in calendar entry data: {str(e)}",
                )
            except ValueError as e:
                self.add_error(
                    "calendar_entry", f"Invalid calendar entry data: {str(e)}"
                )
            except Exception as e:
                self.add_error(
                    "calendar_entry", f"Error processing calendar entry data: {str(e)}"
                )

        cleaned_data["calendar_entry"] = getattr(self, "calendar_entry_data", {})
        logger.info(f"Cleaned data: {cleaned_data}")

        return cleaned_data
