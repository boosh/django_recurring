from django import forms
from django.contrib import admin

from .models import Timezone, RecurrenceRule, RecurrenceSet, RecurrenceSetRule, RecurrenceDate
from .widgets import RRuleWidget


class RecurrenceRuleForm(forms.ModelForm):
    class Meta:
        model = RecurrenceRule
        fields = '__all__'
        widgets = {
            'frequency': RRuleWidget(),
        }


class RecurrenceRuleAdmin(admin.ModelAdmin):
    form = RecurrenceRuleForm


admin.site.register(Timezone)
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
admin.site.register(RecurrenceSet)
admin.site.register(RecurrenceSetRule)
admin.site.register(RecurrenceDate)
