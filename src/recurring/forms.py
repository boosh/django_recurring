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
            self.initial['recurrence_set'] = self.instance.to_ical()

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
            self.rule_formset.instance = instance
            self.rule_formset.save()
            
            # Save dates manually
            RecurrenceDate.objects.filter(recurrence_set=instance).delete()
            for date_data in self.cleaned_data.get('dates', []):
                RecurrenceDate.objects.create(
                    recurrence_set=instance,
                    date=date_data['date'],
                    is_exclusion=date_data['is_exclusion']
                )
            
            instance.recalculate_occurrences()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        # Validate rule formset
        if self.rule_formset.is_valid():
            for form in self.rule_formset.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    # Process valid rule form data
                    pass
        else:
            self.add_error(None, f"Rule formset errors: {self.rule_formset.errors}")

        # Validate date formset
        if self.date_formset.is_valid():
            for form in self.date_formset.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    # Process valid date form data
                    date = form.cleaned_data.get('date')
                    is_exclusion = form.cleaned_data.get('is_exclusion', False)
                    if date:
                        # Add the date to the cleaned_data
                        if 'dates' not in cleaned_data:
                            cleaned_data['dates'] = []
                        cleaned_data['dates'].append({'date': date, 'is_exclusion': is_exclusion})
        else:
            self.add_error(None, f"Date formset errors: {self.date_formset.errors}")

        # Check if at least one rule or date is added
        if not self.rule_formset.forms and not self.date_formset.forms:
            self.add_error(None, "You must add at least one rule or date to the recurrence set.")

        return cleaned_data
