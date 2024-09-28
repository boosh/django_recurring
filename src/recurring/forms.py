from django import forms

from .models import RecurrenceSet, RecurrenceRule
from .widgets import RecurrenceSetWidget, RecurrenceRuleWidget


class RecurrenceSetForm(forms.ModelForm):
    class Meta:
        model = RecurrenceSet
        fields = '__all__'
        widgets = {
            'recurrence_set': RecurrenceSetWidget(),
        }


class RecurrenceRuleForm(forms.ModelForm):
    class Meta:
        model = RecurrenceRule
        fields = '__all__'
        widgets = {
            'recurrence_rule': RecurrenceRuleWidget(),
        }
