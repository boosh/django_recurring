from django import forms
from django.contrib import admin
from django.contrib import messages

from .forms import (
    RecurrenceRuleForm,
    RecurrenceSetForm,
)
from .models import (
    Timezone,
    RecurrenceRule,
    RecurrenceSet,
)


class RecurrenceRuleAdmin(admin.ModelAdmin):
    form = RecurrenceRuleForm


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
                ical_data = form.cleaned_data['recurrence_set']
                if ical_data:
                    # Clear existing rules and dates
                    obj.recurrencesetrules.all().delete()
                    obj.dates.all().delete()

                    # Create new RecurrenceSet from iCal data
                    new_set = RecurrenceSet.from_ical(ical_data)

                    # Copy rules and dates from new_set to obj
                    for rule in new_set.recurrencesetrules.all():
                        rule.pk = None
                        rule.recurrence_set = obj
                        rule.save()
                    for date in new_set.dates.all():
                        date.pk = None
                        date.recurrence_set = obj
                        date.save()

                    # Delete the temporary RecurrenceSet
                    new_set.delete()

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
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
admin.site.register(RecurrenceSet, RecurrenceSetAdmin)
