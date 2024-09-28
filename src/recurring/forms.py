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
        fields = ["recurrence_rule", "is_exclusion"]


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
    class Meta:
        model = RecurrenceSet
        fields = ["name", "description", "timezone"]
        widgets = {
            "recurrence_set": RecurrenceSetWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            self.date_formset.instance = instance
            self.date_formset.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        formset_errors = []
        if not self.rule_formset.is_valid():
            formset_errors.append(f"Rule formset errors: {self.rule_formset.errors}")
        if not self.date_formset.is_valid():
            formset_errors.append(f"Date formset errors: {self.date_formset.errors}")

        if formset_errors:
            raise forms.ValidationError(
                "Please correct the errors in the formsets:\n" + "\n".join(formset_errors)
            )

        # Add more detailed error checking
        if not self.rule_formset.forms and not self.date_formset.forms:
            raise forms.ValidationError("You must add at least one rule or date to the recurrence set.")

        for form in self.rule_formset.forms:
            if form.errors:
                raise forms.ValidationError(f"Error in rule: {form.errors}")

        for form in self.date_formset.forms:
            if form.errors:
                raise forms.ValidationError(f"Error in date: {form.errors}")

        return cleaned_data
