import json
import logging

from django import forms
from django.utils.dateparse import parse_datetime

from .models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, RecurrenceRuleDateRange
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
            instance.save(recalculate=False)  # Save without recalculating

            logger.info("Processing recurrence_set data")
            recurrence_set_data = self.cleaned_data.get('recurrence_set')
            if recurrence_set_data:
                logger.info(f"Recurrence set data: {recurrence_set_data}")
                recurrence_set_dict = json.loads(recurrence_set_data)

                logger.info("Clearing existing rules")
                instance.recurrencesetrules.all().delete()

                logger.info("Adding new rules and date ranges")
                for rule_data in recurrence_set_dict.get('rules', []):
                    rule = RecurrenceRule.from_dict(rule_data['rule'])
                    rule.save()
                    recurrence_set_rule = RecurrenceSetRule.objects.create(
                        recurrence_set=instance,
                        recurrence_rule=rule,
                        is_exclusion=rule_data.get('is_exclusion', False)
                    )

                    for date_range_data in rule_data.get('dateRanges', []):
                        RecurrenceRuleDateRange.objects.create(
                            recurrence_rule=rule,
                            start_date=parse_datetime(date_range_data['startDate']),
                            end_date=parse_datetime(date_range_data['endDate']),
                            is_exclusion=date_range_data.get('isExclusion', False)
                        )

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

                    # Create a new rule dictionary with the expected structure
                    new_rule_data = {
                        'rule': {
                            'frequency': rule_data['frequency'],
                            'interval': rule_data['interval'],
                            'byweekday': rule_data['byweekday'],
                            'bymonth': rule_data['bymonth'],
                            'bymonthday': rule_data['bymonthday'],
                            'bysetpos': rule_data['bysetpos'],
                        },
                        'is_exclusion': rule_data.get('isExclusion', False),
                        'date_ranges': []
                    }

                    # Process date ranges
                    if 'dateRanges' not in rule_data or not isinstance(rule_data['dateRanges'], list):
                        raise ValueError("Each rule must contain a 'dateRanges' list")
                    for date_range_data in rule_data['dateRanges']:
                        if not isinstance(date_range_data, dict):
                            raise ValueError("Each date range must be a dictionary")
                        if 'startDate' not in date_range_data or 'endDate' not in date_range_data:
                            raise ValueError("Each date range must have 'startDate' and 'endDate'")
                        new_rule_data['date_ranges'].append({
                            'start_date': date_range_data['startDate'],
                            'end_date': date_range_data['endDate'],
                            'is_exclusion': date_range_data.get('isExclusion', False)
                        })

                    rule = RecurrenceRule.from_dict(new_rule_data['rule'])
                    rules_to_add.append((rule, new_rule_data['is_exclusion'], new_rule_data['date_ranges']))

                # Store the processed data
                self.rules_to_add = rules_to_add

            except json.JSONDecodeError:
                self.add_error('recurrence_set', "Invalid JSON data for recurrence set.")
            except ValueError as e:
                self.add_error('recurrence_set', f"Invalid recurrence set data: {str(e)}")
            except Exception as e:
                self.add_error('recurrence_set', f"Error processing recurrence set data: {str(e)}")

        # Check if at least one rule with a date range is added
        if not getattr(self, 'rules_to_add', []) or not any(rule_data.get('dateRanges') for rule_data in recurrence_set_dict.get('rules', [])):
            self.add_error(None, "You must add at least one rule with a date range to the recurrence set.")

        logger.info(f"Cleaned data: {cleaned_data}")

        return cleaned_data
