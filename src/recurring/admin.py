from django.contrib import admin

from .forms import RecurrenceRuleForm
from .models import Timezone, RecurrenceRule, RecurrenceSet, RecurrenceSetRule, RecurrenceDate


class RecurrenceRuleAdmin(admin.ModelAdmin):
    form = RecurrenceRuleForm


admin.site.register(Timezone)
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)
admin.site.register(RecurrenceSet)
admin.site.register(RecurrenceSetRule)
admin.site.register(RecurrenceDate)
