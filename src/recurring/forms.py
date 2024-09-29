import json
import logging

from django import forms

from .models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, RecurrenceDate
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
        self.fields['recurrence_set'].widget = RecurrenceSetWidget(form=self)
        self.fields['recurrence_set'].widget.attrs['style'] = 'display: none;'

        # Populate the recurrence_set field with existing data
        if self.instance.pk:
            recurrence_set_data = self.instance.to_dict()
            self.initial['recurrence_set'] = json.dumps(recurrence_set_data)
            self.fields['recurrence_set'].widget.attrs['data-initial'] = json.dumps(recurrence_set_data)

    def save(self, commit: bool = True):
        logger.info("Starting save method")
        instance = super().save(commit=False)
        if commit:
            logger.info("Commit is True, saving instance")
            instance.save()

            logger.info("Processing recurrence_set data")
            recurrence_set_data = self.cleaned_data.get('recurrence_set')
            if recurrence_set_data:
                logger.info(f"Recurrence set data: {recurrence_set_data}")
                recurrence_set_dict = json.loads(recurrence_set_data)

                logger.info("Clearing existing rules and dates")
                instance.recurrencesetrules.all().delete()
                instance.dates.all().delete()

                logger.info("Adding new rules")
                for rule_data in recurrence_set_dict.get('rules', []):
                    rule = RecurrenceRule.from_dict(rule_data)
                    rule.save()
                    RecurrenceSetRule.objects.create(
                        recurrence_set=instance,
                        recurrence_rule=rule,
                        is_exclusion=rule_data.get('is_exclusion', False)
                    )

                logger.info("Adding new dates")
                for date_data in recurrence_set_dict.get('dates', []):
                    RecurrenceDate.objects.create(
                        recurrence_set=instance,
                        date=date_data['date'],
                        is_exclusion=date_data.get('is_exclusion', False)
                    )

            logger.info("Recalculating occurrences")
            instance.recalculate_occurrences()

        logger.info("Save method completed")
        return instance

    def clean(self):
        logger.info("Inside clean")
        cleaned_data = super().clean()

        if self.errors:
            logger.info("Returning errors")
            return cleaned_data

        logger.info("No form errors")
        recurrence_set_data = cleaned_data.get('recurrence_set')
        if recurrence_set_data:
            try:
                # Process the recurrence_set data
                recurrence_set_dict = json.loads(recurrence_set_data)

                # Validate the structure of recurrence_set_dict
                if not isinstance(recurrence_set_dict, dict):
                    raise ValueError("Recurrence set data must be a dictionary")

                if 'rules' not in recurrence_set_dict or not isinstance(recurrence_set_dict['rules'], list):
                    raise ValueError("Recurrence set data must contain a 'rules' list")

                if 'dates' not in recurrence_set_dict or not isinstance(recurrence_set_dict['dates'], list):
                    raise ValueError("Recurrence set data must contain a 'dates' list")

                # Process rules
                rules_to_add = []
                for rule_data in recurrence_set_dict['rules']:
                    if not isinstance(rule_data, dict):
                        raise ValueError("Each rule must be a dictionary")
                    rule = RecurrenceRule.from_dict(rule_data)
                    rules_to_add.append((rule, rule_data.get('is_exclusion', False)))

                # Process dates
                dates_to_add = []
                for date_data in recurrence_set_dict['dates']:
                    if not isinstance(date_data, dict):
                        raise ValueError("Each date must be a dictionary")
                    dates_to_add.append((date_data['date'], date_data.get('is_exclusion', False)))

                # Store the processed data
                self.rules_to_add = rules_to_add
                self.dates_to_add = dates_to_add

            except json.JSONDecodeError:
                self.add_error('recurrence_set', "Invalid JSON data for recurrence set.")
            except ValueError as e:
                self.add_error('recurrence_set', f"Invalid recurrence set data: {str(e)}")
            except Exception as e:
                self.add_error('recurrence_set', f"Error processing recurrence set data: {str(e)}")

        # Check if at least one rule or date is added
        if not getattr(self, 'rules_to_add', []) and not getattr(self, 'dates_to_add', []):
            self.add_error(None, "You must add at least one rule or date to the recurrence set.")

        logger.info(f"Cleaned data: {cleaned_data}")

        return cleaned_data
