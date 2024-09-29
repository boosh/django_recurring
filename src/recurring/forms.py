import json

from django import forms
from django.forms import inlineformset_factory

from .models import RecurrenceSet, RecurrenceRule, RecurrenceSetRule, RecurrenceDate
from .widgets import RecurrenceSetWidget, RecurrenceRuleWidget


class RecurrenceRuleForm(forms.ModelForm):
    class Meta:
        model = RecurrenceRule
        fields = "__all__"
        widgets = {
            "recurrence_rule": RecurrenceRuleWidget(),
        }


class RecurrenceSetRuleForm(forms.ModelForm):
    class Meta:
        model = RecurrenceSetRule
        fields = ["is_exclusion", 'recurrence_rule']
        widgets = {
            "is_exclusion": forms.HiddenInput(),
            "recurrence_rule": forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def is_valid(self):
        valid = super().is_valid()
        if not hasattr(self, 'cleaned_data'):
            self.cleaned_data = {}
        return valid


class RecurrenceDateForm(forms.ModelForm):
    class Meta:
        model = RecurrenceDate
        fields = ["date", "is_exclusion"]


RecurrenceSetRuleFormSet = inlineformset_factory(
    RecurrenceSet,
    RecurrenceSetRule,
    form=RecurrenceSetRuleForm,
    extra=1,
    can_delete=True,
)

RecurrenceDateFormSet = inlineformset_factory(
    RecurrenceSet, RecurrenceDate, form=RecurrenceDateForm, extra=1, can_delete=True
)


class RecurrenceSetForm(forms.ModelForm):
    recurrence_set = forms.CharField(required=False, widget=RecurrenceSetWidget)

    class Meta:
        model = RecurrenceSet
        fields = ["name", "description", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recurrence_set'].widget = RecurrenceSetWidget(form=self)
        self.fields['recurrence_set'].widget.attrs['style'] = 'display: none;'
        if self.instance.pk:
            self.rule_formset = RecurrenceSetRuleFormSet(
                instance=self.instance,
                data=self.data if self.is_bound else None,
                prefix="rules"
            )
            self.date_formset = RecurrenceDateFormSet(
                instance=self.instance,
                data=self.data if self.is_bound else None,
                prefix="dates"
            )
        else:
            self.rule_formset = RecurrenceSetRuleFormSet(
                data=self.data if self.is_bound else None,
                prefix="rules"
            )
            self.date_formset = RecurrenceDateFormSet(
                data=self.data if self.is_bound else None,
                prefix="dates"
            )

        # Populate the recurrence_set field with existing data
        if self.instance.pk:
            self.initial['recurrence_set'] = json.dumps(self.instance.to_dict())

    def is_valid(self):
        return all(
            [
                super().is_valid(),
                self.rule_formset.is_valid(),
                self.date_formset.is_valid(),
            ]
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            
            # Add rules and dates for new instances
            if hasattr(self, 'rules_to_add'):
                for rule in self.rules_to_add:
                    rule.pk = None
                    rule.recurrence_set = instance
                    rule.save()
            
            if hasattr(self, 'dates_to_add'):
                for date in self.dates_to_add:
                    date.pk = None
                    date.recurrence_set = instance
                    date.save()
            
            instance.recalculate_occurrences()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        recurrence_set_data = cleaned_data.get('recurrence_set')
        if recurrence_set_data:
            try:
                # Process the recurrence_set data
                recurrence_set_dict = json.loads(recurrence_set_data)
                recurrence_set = RecurrenceSet.from_dict(recurrence_set_dict)

                # Clear existing rules and dates only if the instance has been saved
                if self.instance.pk:
                    self.instance.recurrencesetrules.all().delete()
                    self.instance.dates.all().delete()

                    # Add new rules
                    for rule in recurrence_set.recurrencesetrules.all():
                        rule.pk = None
                        rule.recurrence_set = self.instance
                        rule.save()

                    # Add new dates
                    for date in recurrence_set.dates.all():
                        date.pk = None
                        date.recurrence_set = self.instance
                        date.save()
                else:
                    # Store the rules and dates to be added after the instance is saved
                    self.rules_to_add = recurrence_set.recurrencesetrules.all()
                    self.dates_to_add = recurrence_set.dates.all()

            except json.JSONDecodeError:
                self.add_error('recurrence_set', "Invalid JSON data for recurrence set.")
            except Exception as e:
                self.add_error('recurrence_set', f"Error processing recurrence set data: {str(e)}")

        # Check if at least one rule or date is added only if the instance has been saved
        if self.instance.pk and not self.instance.recurrencesetrules.exists() and not self.instance.dates.exists():
            self.add_error(None, "You must add at least one rule or date to the recurrence set.")

        return cleaned_data
