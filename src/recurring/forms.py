import json
import logging
from datetime import datetime

import pytz
from django import forms

from .models import RecurrenceSet
from .utils import recursive_camel_to_snake, recursive_snake_to_camel
from .widgets import RecurrenceSetWidget

logger = logging.getLogger(__name__)


class RecurrenceSetForm(forms.ModelForm):
    recurrence_set = forms.CharField(required=False, widget=RecurrenceSetWidget)

    class Meta:
        model = RecurrenceSet
        fields = ["name", "description", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Form init method")
        self.fields["recurrence_set"].widget = RecurrenceSetWidget(form=self)
        self.fields["recurrence_set"].widget.attrs["style"] = "display: none;"

        # Populate the recurrence_set field with existing data
        if self.instance.pk:
            recurrence_set_data = self.instance.to_dict()
            self.initial["recurrence_set"] = json.dumps(recurrence_set_data)
            camelised = recursive_snake_to_camel(recurrence_set_data)
            self.fields["recurrence_set"].widget.attrs["data-initial"] = json.dumps(
                camelised
            )

    def save(self, commit: bool = True):
        logger.info(f"Starting save method (commit={commit})")
        instance = super().save(commit=False)
        if commit:
            logger.info("Commit is True, saving instance")
            instance.save(recalculate=False)  # Save without recalculating

            logger.info("Processing recurrence_set data")
            recurrence_set_data = self.cleaned_data.get("recurrence_set")
            if recurrence_set_data:
                logger.info("Clearing existing rules")
                [rule.delete() for rule in instance.recurrencesetrules.all()]

                logger.info("Adding new rules and date ranges")
                instance.from_dict(recurrence_set_data)

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
        recurrence_set_data = cleaned_data.get("recurrence_set")
        if recurrence_set_data:
            try:
                # Process the recurrence_set data
                recurrence_set_dict_camel = json.loads(recurrence_set_data)

                # Validate the structure of recurrence_set_dict
                if not isinstance(recurrence_set_dict_camel, dict):
                    raise ValueError("Recurrence set data must be a dictionary")

                # recursively convert all keys to snake case for consistency
                recurrence_set_dict = recursive_camel_to_snake(
                    recurrence_set_dict_camel
                )
                self.recurrence_set_data = recurrence_set_dict

                if not isinstance(recurrence_set_dict["rules"], list):
                    raise ValueError("Recurrence set data must contain a 'rules' list")

                # Validate the structure
                if not isinstance(recurrence_set_dict.get("rules"), list):
                    raise ValueError("Recurrence set data must contain a 'rules' list")

                for rule_data in recurrence_set_dict["rules"]:
                    if not isinstance(rule_data, dict):
                        raise ValueError("Each rule must be a dictionary")
                    if "rule" not in rule_data:
                        raise ValueError("Each rule must contain a 'rule' key")
                    if not isinstance(rule_data.get("date_ranges"), list):
                        raise ValueError("Each rule must contain a 'date_ranges' list")

                    for date_range_data in rule_data["date_ranges"]:
                        if not isinstance(date_range_data, dict):
                            raise ValueError("Each date range must be a dictionary")
                        if (
                            "start_date" not in date_range_data
                            or "end_date" not in date_range_data
                        ):
                            raise ValueError(
                                "Each date range must have 'start_date' and 'end_date'"
                            )

                        # Convert start_date and end_date to timezone-aware datetimes
                        start_date = datetime.fromisoformat(
                            date_range_data["start_date"]
                        )
                        end_date = datetime.fromisoformat(date_range_data["end_date"])

                        # Get the submitted timezone
                        submitted_timezone = pytz.timezone(
                            cleaned_data.get("timezone").name
                        )

                        date_range_data["start_date"] = submitted_timezone.localize(
                            start_date
                        )
                        date_range_data["end_date"] = submitted_timezone.localize(
                            end_date
                        )

            except json.JSONDecodeError:
                self.add_error(
                    "recurrence_set", "Invalid JSON data for recurrence set."
                )
            except KeyError as e:
                self.add_error(
                    "recurrence_set",
                    f"Missing required key in recurrence set data: {str(e)}",
                )
            except ValueError as e:
                self.add_error(
                    "recurrence_set", f"Invalid recurrence set data: {str(e)}"
                )
            except Exception as e:
                self.add_error(
                    "recurrence_set", f"Error processing recurrence set data: {str(e)}"
                )

        # Check if at least one rule with a date range is added
        if not hasattr(self, "recurrence_set_data") or not any(
            rule_data["date_ranges"]
            for rule_data in self.recurrence_set_data.get("rules", [])
        ):
            self.add_error(
                None,
                "You must add at least one rule with a date range to the recurrence set.",
            )

        cleaned_data["recurrence_set"] = getattr(self, "recurrence_set_data", {})
        logger.info(f"Cleaned data: {cleaned_data}")

        return cleaned_data
