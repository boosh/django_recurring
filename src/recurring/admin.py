from django import forms
from django.contrib import admin
from django.contrib import messages

from .forms import (
    RecurrenceSetForm,
)
from .models import (
    Timezone,
    RecurrenceSet,
)


class RecurrenceSetAdmin(admin.ModelAdmin):
    form = RecurrenceSetForm
    list_display = ("name", "timezone", "next_occurrence", "previous_occurrence")
    search_fields = ("name",)
    list_filter = ("timezone",)
    readonly_fields = ("ical_string",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def ical_string(self, obj):
        return obj.to_ical()

    ical_string.short_description = "iCal String"

    def save_model(self, request, obj, form, change):
        try:
            form.save()
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
