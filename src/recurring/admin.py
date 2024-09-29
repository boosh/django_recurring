import json

from django import forms
from django.contrib import admin
from django.contrib import messages

from .forms import (
    RecurrenceSetForm,
)
from .models import (
    Timezone,
    RecurrenceRule,
    RecurrenceSet, RecurrenceSetRule, RecurrenceDate,
)


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
                    # Clear existing rules and dates
                    obj.recurrencesetrules.all().delete()
                    obj.dates.all().delete()

                    # Create new RecurrenceSet from JSON data
                    recurrence_set_dict = json.loads(recurrence_set_data)

                    # Add rules
                    for rule_data in recurrence_set_dict.get('rules', []):
                        rule = RecurrenceRule.from_dict(rule_data)
                        rule.save()
                        RecurrenceSetRule.objects.create(
                            recurrence_set=obj,
                            recurrence_rule=rule,
                            is_exclusion=rule_data.get('is_exclusion', False)
                        )

                    # Add dates
                    for date_data in recurrence_set_dict.get('dates', []):
                        RecurrenceDate.objects.create(
                            recurrence_set=obj,
                            date=date_data['date'],
                            is_exclusion=date_data.get('is_exclusion', False)
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
