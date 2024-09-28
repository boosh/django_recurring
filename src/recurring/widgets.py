from django import forms
from django.utils.safestring import mark_safe


class RRuleWidget(forms.Widget):
    template_name = 'admin/recurring/rrule_widget.html'

    class Media:
        js = ('admin/js/vendor/rrule.min.js', 'admin/js/rrule_widget.js')
        css = {
            'all': ('admin/css/rrule_widget.css',)
        }

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(renderer.render(self.template_name, context))
