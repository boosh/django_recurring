from django import forms
from django.utils.safestring import mark_safe

from .models import RecurrenceRule


class RecurrenceSetWidget(forms.Widget):
    template_name = "admin/recurring/recurrence_set_widget.html"

    class Media:
        js = ("admin/js/vendor/rrule.min.js", "admin/js/recurrence_set_widget.js")
        css = {"all": ("admin/css/recurrence_set_widget.css",)}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        if value is None:
            value = ""
        context["widget"]["value"] = value
        context["recurrence_rules"] = RecurrenceRule.objects.all()

        # Add formsets to the context
        if hasattr(self.form, "rule_formset") and hasattr(self.form, "date_formset"):
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
