import json

from django import forms
from django.core import serializers
from django.utils.safestring import mark_safe

from .models import RecurrenceRule


class RecurrenceSetWidget(forms.Widget):
    template_name = "admin/recurring/recurrence_set_widget.html"

    class Media:
        js = ("admin/js/vendor/rrule.min.js", "admin/js/rrule_widget.js")
        css = {"all": ("admin/css/rrule_widget.css",)}

    def __init__(self, attrs=None, form=None):
        super().__init__(attrs)
        self.form = form

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        if value is None:
            value = ""
        context["widget"]["value"] = value

        # Serialize RecurrenceRule queryset to JSON
        recurrence_rules = RecurrenceRule.objects.all()
        serialized_rules = serializers.serialize('json', recurrence_rules)
        context["recurrence_rules"] = mark_safe(json.dumps(json.loads(serialized_rules)))

        # Add formsets to the context
        if self.form and hasattr(self.form, "rule_formset") and hasattr(self.form, "date_formset"):
            context["rule_formset"] = self.form.rule_formset
            context["date_formset"] = self.form.date_formset

        return mark_safe(renderer.render(self.template_name, context))


class RecurrenceRuleWidget(forms.Widget):
    template_name = "admin/recurring/recurrence_rule_widget.html"

    class Media:
        js = ("admin/js/vendor/rrule.min.js", "admin/js/recurrence_rule_widget.js")
        css = {"all": ("admin/css/recurrence_rule_widget.css",)}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        if value is None:
            value = ""
        context["widget"]["value"] = value
        return mark_safe(renderer.render(self.template_name, context))
