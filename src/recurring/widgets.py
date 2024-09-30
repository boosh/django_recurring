import json
import logging

from django import forms
from django.utils.safestring import mark_safe

from .models import RecurrenceRule
from .utils import recursive_snake_to_camel

logger = logging.getLogger(__name__)


class RecurrenceSetWidget(forms.Widget):
    template_name = "admin/recurring/recurrence_set_widget.html"

    class Media:
        js = ("admin/js/vendor/rrule.min.js", "admin/js/rrule_widget.js")
        css = {"all": ("admin/css/rrule_widget.css",)}

    def __init__(self, attrs=None, form=None):
        super().__init__(attrs)
        self.form = form
        if self.form and self.form.instance and self.form.instance.pk:
            recurrence_set = self.form.instance
            recurrence_set_data = recurrence_set.to_dict()
            recurrence_set_data["id"] = recurrence_set.pk
            for rule in recurrence_set_data["rules"]:
                rule_obj = RecurrenceRule.objects.get(id=rule["rule"]["id"])
                rule["date_ranges"] = [
                    {
                        "start_date": date_range.start_date.isoformat(),
                        "end_date": date_range.end_date.isoformat(),
                        "is_exclusion": date_range.is_exclusion,
                    }
                    for date_range in rule_obj.date_ranges.all()
                ]
            self.initial = json.dumps(recursive_snake_to_camel(recurrence_set_data))

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(self.attrs, attrs)
        context = self.get_context(name, value, final_attrs)
        if value is None:
            value = ""
        # ignore value because it doesn't include the date ranges
        context["widget"]["value"] = self.initial if hasattr(self, "initial") else value

        if hasattr(self, "initial"):
            context["widget"]["attrs"]["data-initial"] = self.initial
            logger.info(f"Set initial data to {self.initial}")

        return mark_safe(renderer.render(self.template_name, context))
