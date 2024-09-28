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
            form.rule_formset = RecurrenceSetRuleFormSet(instance=obj, prefix="rules")
            form.date_formset = RecurrenceDateFormSet(instance=obj, prefix="dates")
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form.rule_formset.instance = obj
        form.rule_formset.save()
        form.date_formset.instance = obj
        form.date_formset.save()


admin.site.register(Timezone)
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
admin.site.register(RecurrenceSet, RecurrenceSetAdmin)
admin.site.register(RecurrenceSetRule)
admin.site.register(RecurrenceDate)
