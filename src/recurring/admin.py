from django import forms
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.text import slugify

from .forms import (
    CalendarEntryForm,
)
from .models import (
    Timezone,
    CalendarEntry,
)


# Uncomment these if you're debugging things, otherwise they'll
# probably just confuse admins
# @admin.register(RecurrenceRule)
# class RecurrenceRuleAdmin(admin.ModelAdmin):
#     pass
#
#
# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     pass
#
#
# @admin.register(ExclusionDateRange)
# class ExclusionDateRangeAdmin(admin.ModelAdmin):
#     pass


@admin.action(description="Recalculate occurrences for selected")
def recalculate_occurrences(modeladmin, request, queryset):
    count = 0
    for entry in queryset:
        entry.calculate_occurrences()
        count += 1

    messages.success(
        request, f"Successfully recalculated occurrences for {count} calendar entries."
    )


class CalendarEntryAdmin(admin.ModelAdmin):
    form = CalendarEntryForm
    list_display = (
        "name",
        "timezone",
        "first_occurrence",
        "previous_occurrence",
        "next_occurrence",
        "last_occurrence",
    )
    actions = [recalculate_occurrences]
    search_fields = ("name",)
    list_filter = ("timezone",)
    readonly_fields = ("updated_at", "ical_string", "ical_download_link")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def ical_string(self, obj):
        return obj.to_ical()

    ical_string.short_description = "iCal String"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/download-ical/",
                self.admin_site.admin_view(self.download_ical),
                name="%s_%s_download_ical"
                % (self.model._meta.app_label, self.model._meta.model_name),
            ),
        ]
        return custom_urls + urls

    def ical_download_link(self, obj):
        url = reverse(
            "admin:%s_%s_download_ical" % (obj._meta.app_label, obj._meta.model_name),
            args=[obj.pk],
        )
        return format_html('<a href="{}">Download iCal</a>', url)

    ical_download_link.short_description = "Download iCal"

    def download_ical(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            return HttpResponse("Object not found", status=404)

        ical_string = obj.to_ical()
        response = HttpResponse(ical_string, content_type="text/calendar")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{slugify(obj.name)}.ics"'
        return response

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
admin.site.register(CalendarEntry, CalendarEntryAdmin)
