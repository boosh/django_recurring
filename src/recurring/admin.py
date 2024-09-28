from django.contrib import admin

from .forms import (
    RecurrenceRuleForm,
    RecurrenceSetForm,
    RecurrenceSetRuleFormSet,
    RecurrenceDateFormSet,
)
from .models import (
    Timezone,
    RecurrenceRule,
    RecurrenceSet,
    RecurrenceSetRule,
    RecurrenceDate,
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
        if obj:
            form.rule_formset = RecurrenceSetRuleFormSet(instance=obj)
            form.date_formset = RecurrenceDateFormSet(instance=obj)
        else:
            form.rule_formset = RecurrenceSetRuleFormSet()
            form.date_formset = RecurrenceDateFormSet()
        return form

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except forms.ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return

    def save_related(self, request, form, formsets, change):
        try:
            super().save_related(request, form, formsets, change)
            form.save_m2m()
            form.rule_formset.save()
            form.date_formset.save()
        except forms.ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    def save_formset(self, request, form, formset, change):
        try:
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                instance.save()
            formset.save_m2m()
        except forms.ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)


admin.site.register(Timezone)
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
admin.site.register(RecurrenceSet, RecurrenceSetAdmin)
admin.site.register(RecurrenceSetRule)
admin.site.register(RecurrenceDate)
