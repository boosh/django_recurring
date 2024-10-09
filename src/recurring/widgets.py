import json
import logging

from django import forms
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class CalendarEntryWidget(forms.Widget):
    template_name = "admin/recurring/calendar_entry_widget.html"

    class Media:
        js = (
            "admin/js/vendor/luxon-3.5.0.min.js",
            "admin/js/calendar_entry_widget.js",
        )
        css = {"all": ("admin/css/calendar_entry_widget.css",)}

    def __init__(self, attrs=None, form=None):
        super().__init__(attrs)
        self.form = form
        if self.form and self.form.instance and self.form.instance.pk:
            calendar_entry = self.form.instance
            calendar_entry_data = calendar_entry.to_dict()
            calendar_entry_data["id"] = calendar_entry.pk
            self.initial = json.dumps(calendar_entry_data)

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(self.attrs, attrs)
        context = self.get_context(name, value, final_attrs)
        if value is None:
            value = ""
        context["widget"]["value"] = self.initial if hasattr(self, "initial") else value

        if hasattr(self, "initial"):
            context["widget"]["attrs"]["data-initial"] = self.initial
            logger.info(f"Set initial data to {self.initial}")

        return mark_safe(renderer.render(self.template_name, context))
