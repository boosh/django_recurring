import json
import logging
from datetime import datetime

import pytz
from django import forms

from .models import CalendarEntry
from .utils import recursive_camel_to_snake, recursive_snake_to_camel
from .widgets import CalendarEntryWidget

logger = logging.getLogger(__name__)


class CalendarEntryForm(forms.ModelForm):
    calendar_entry = forms.CharField(required=False, widget=CalendarEntryWidget)

    class Meta:
        model = CalendarEntry
        fields = ["name", "description", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Form init method")
        self.fields["calendar_entry"].widget = CalendarEntryWidget(form=self)
        self.fields["calendar_entry"].widget.attrs["style"] = "display: none;"

        if self.instance.pk:
            calendar_entry_data = self.instance.to_dict()
            self.initial["calendar_entry"] = json.dumps(calendar_entry_data)
            camelised = recursive_snake_to_camel(calendar_entry_data)
            self.fields["calendar_entry"].widget.attrs["data-initial"] = json.dumps(
                camelised
            )

    def save(self, commit: bool = True):
        logger.info(f"Starting save method (commit={commit})")
        instance = super().save(commit=False)
        if commit:
            logger.info("Commit is True, saving instance")
            instance.save(recalculate=False)  # Save without recalculating

            logger.info("Processing calendar_entry data")
            calendar_entry_data = self.cleaned_data.get("calendar_entry")
            if calendar_entry_data:
                logger.info("Clearing existing events")
                instance.events.all().delete()

                logger.info("Adding new events and exclusions")
                instance.from_dict(calendar_entry_data)

            logger.info("Recalculating occurrences")
            instance.recalculate_occurrences()
            instance.save()  # Save to ensure the recalculated occurrences are stored

        logger.info("Save method completed")
        return instance

    def clean(self):
        logger.info("Inside clean")
        cleaned_data = super().clean()

        if self.errors:
            logger.info("Returning errors")
            return cleaned_data

        logger.info("No form errors")
        calendar_entry_data = cleaned_data.get("calendar_entry")
        if calendar_entry_data:
            try:
                calendar_entry_dict_camel = json.loads(calendar_entry_data)

                if not isinstance(calendar_entry_dict_camel, dict):
                    raise ValueError("Calendar entry data must be a dictionary")

                calendar_entry_dict = recursive_camel_to_snake(
                    calendar_entry_dict_camel
                )
                self.calendar_entry_data = calendar_entry_dict

                if not isinstance(calendar_entry_dict.get("events"), list):
                    raise ValueError(
                        "Calendar entry data must contain an 'events' list"
                    )

                # Get the submitted timezone
                submitted_timezone = pytz.timezone(cleaned_data.get("timezone").name)

                for event_data in calendar_entry_dict["events"]:
                    if not isinstance(event_data, dict):
                        raise ValueError("Each event must be a dictionary")
                    if (
                        "start_date_time" not in event_data
                        or "end_date_time" not in event_data
                    ):
                        raise ValueError(
                            "Each event must have 'start_date_time' and 'end_date_time'"
                        )

                    # Convert start_date_time and end_date_time to timezone-aware datetimes
                    start_time = datetime.fromisoformat(event_data["start_date_time"])
                    end_time = datetime.fromisoformat(event_data["end_date_time"])

                    event_data["start_date_time"] = submitted_timezone.localize(
                        start_time
                    )
                    event_data["end_date_time"] = submitted_timezone.localize(end_time)

                    # Rule and exclusions are optional
                    if "rule" in event_data:
                        if not isinstance(event_data["rule"], dict):
                            raise ValueError("Event rule must be a dictionary")

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

                            exclusion_data["start_date"] = submitted_timezone.localize(
                                exclusion_start
                            )
                            exclusion_data["end_date"] = submitted_timezone.localize(
                                exclusion_end
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

        # Check if at least one event is added
        if not hasattr(self, "calendar_entry_data") or not self.calendar_entry_data.get(
            "events"
        ):
            self.add_error(
                None, "You must add at least one event to the calendar entry."
            )

        cleaned_data["calendar_entry"] = getattr(self, "calendar_entry_data", {})
        logger.info(f"Cleaned data: {cleaned_data}")

        return cleaned_data
