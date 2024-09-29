import json

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.utils.dateparse import parse_datetime

from .forms import (
    RecurrenceSetForm,
)
from .models import (
    Timezone,
    RecurrenceRule,
    RecurrenceSet,
    RecurrenceSetRule,
    RecurrenceRuleDateRange,
)
from .utils import recursive_camel_to_snake


class RecurrenceSetAdmin(admin.ModelAdmin):
    form = RecurrenceSetForm
    list_display = ("name", "timezone", "next_occurrence", "previous_occurrence")
    search_fields = ("name",)
    list_filter = ("timezone",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if 'recurrence_set' in form.cleaned_data:
                recurrence_set_data = form.cleaned_data['recurrence_set']
                if recurrence_set_data:
                    # Clear existing rules
                    obj.recurrencesetrules.all().delete()

                    # Create new RecurrenceSet from JSON data
                    recurrence_set_dict_camel = json.loads(recurrence_set_data)
                    # recursively convert all keys to snake case for consistency
                    recurrence_set_dict = recursive_camel_to_snake(recurrence_set_dict_camel)

                    # Add rules
                    for rule_data in recurrence_set_dict.get('rules', []):
                        rule = RecurrenceRule.from_dict(rule_data)
                        rule.save()
                        RecurrenceSetRule.objects.create(
                            recurrence_set=obj,
                            recurrence_rule=rule,
                            is_exclusion=rule_data.get('is_exclusion', False)
                        )

                    # Add date ranges
                    for rule in obj.recurrencesetrules.all():
                        for date_range_data in rule_data['date_ranges']:
                            RecurrenceRuleDateRange.objects.create(
                                recurrence_rule=rule.recurrence_rule,
                                start_date=parse_datetime(date_range_data['start_date']),
                                end_date=parse_datetime(date_range_data['end_date']),
                                is_exclusion=date_range_data.get('is_exclusion', False)
                            )

                    # Recalculate occurrences
                    obj.recalculate_occurrences()
        except forms.ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.save_m2m()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.save()
        formset.save_m2m()


admin.site.register(Timezone)
admin.site.register(RecurrenceSet, RecurrenceSetAdmin)
