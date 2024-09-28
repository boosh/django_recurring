from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils import timezone
from recurring.admin import RecurrenceSetAdmin
from recurring.forms import RecurrenceSetForm
from recurring.models import RecurrenceSet, Timezone, RecurrenceRule, RecurrenceSetRule, RecurrenceDate
from recurring.widgets import RecurrenceSetWidget, RecurrenceRuleWidget


class MockRequest:
    pass


class RecurrenceSetWidgetTest(TestCase):
    def setUp(self):
        self.timezone = Timezone.objects.create(name="UTC")
        self.recurrence_set = RecurrenceSet.objects.create(
            name="Test Set",
            description="Test Description",
            timezone=self.timezone
        )
        self.site = AdminSite()
        self.admin = RecurrenceSetAdmin(RecurrenceSet, self.site)

    def test_widget_rendering(self):
        request = MockRequest()
        form = self.admin.get_form(request)(instance=self.recurrence_set)

        self.assertIsInstance(form.fields['recurrence_set'].widget, RecurrenceSetWidget)

        rendered = form.fields['recurrence_set'].widget.render(
            'recurrence_set',
            self.recurrence_set.pk,
            attrs={'id': 'id_recurrence_set'}
        )

        self.assertIn('recurrence-set-widget', rendered)
        self.assertIn('id_recurrence_set', rendered)
        self.assertIn('rules-container', rendered)
        self.assertIn('dates-container', rendered)

    def test_widget_media(self):
        widget = RecurrenceSetWidget()
        self.assertIn('admin/js/vendor/rrule.min.js', widget.media._js)
        self.assertIn('admin/js/recurrence_set_widget.js', widget.media._js)
        self.assertIn('admin/css/recurrence_set_widget.css', widget.media._css['all'])

    def test_form_save(self):
        data = {
            'name': 'Updated Test Set',
            'description': 'Updated Description',
            'timezone': self.timezone.pk,
            'recurrence_set': '{"rules":[],"dates":[]}',  # Empty recurrence set
        }
        request = MockRequest()
        form = self.admin.get_form(request)(data, instance=self.recurrence_set)
        self.assertTrue(form.is_valid())

        updated_recurrence_set = form.save()
        self.assertEqual(updated_recurrence_set.name, 'Updated Test Set')
        self.assertEqual(updated_recurrence_set.description, 'Updated Description')

    def test_formsets_in_context(self):
        request = MockRequest()
        form = self.admin.get_form(request)(instance=self.recurrence_set)
        context = form.fields['recurrence_set'].widget.get_context(
            'recurrence_set',
            self.recurrence_set.pk,
            {'id': 'id_recurrence_set'}
        )

        self.assertIn('rule_formset', context)
        self.assertIn('date_formset', context)

    def test_recurrence_rule_widget(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )
        widget = RecurrenceRuleWidget()
        rendered = widget.render('test_rule', rule.pk)
        self.assertIn('recurrence-rule-widget', rendered)
        self.assertIn('recurrence-rule-form', rendered)
        self.assertIn('recurrence-rule-text', rendered)

    def test_recurrence_set_form_with_rules_and_dates(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.WEEKLY,
            interval=2,
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=rule,
            is_exclusion=False
        )
        RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=timezone.now(),
            is_exclusion=False
        )

        form = RecurrenceSetForm(instance=self.recurrence_set)
        self.assertEqual(len(form.rule_formset.forms), 2)  # 1 existing + 1 empty
        self.assertEqual(len(form.date_formset.forms), 2)  # 1 existing + 1 empty

    def test_recurrence_set_form_save_with_rules_and_dates(self):
        data = {
            'name': 'Test Set with Rules and Dates',
            'description': 'Test Description',
            'timezone': self.timezone.pk,
            'rules-TOTAL_FORMS': '1',
            'rules-INITIAL_FORMS': '0',
            'rules-0-recurrence_rule': '',
            'rules-0-is_exclusion': False,
            'dates-TOTAL_FORMS': '1',
            'dates-INITIAL_FORMS': '0',
            'dates-0-date': '2023-01-01 12:00:00',
            'dates-0-is_exclusion': False,
        }
        form = RecurrenceSetForm(data)
        self.assertTrue(form.is_valid())
        recurrence_set = form.save()
        self.assertEqual(recurrence_set.recurrencesetrules.count(), 0)
        self.assertEqual(recurrence_set.dates.count(), 1)

    def test_recurrence_set_to_rruleset(self):
        rule = RecurrenceRule.objects.create(
            frequency=RecurrenceRule.Frequency.DAILY,
            interval=1,
            timezone=self.timezone
        )
        RecurrenceSetRule.objects.create(
            recurrence_set=self.recurrence_set,
            recurrence_rule=rule,
            is_exclusion=False
        )
        RecurrenceDate.objects.create(
            recurrence_set=self.recurrence_set,
            date=timezone.now(),
            is_exclusion=False
        )

        rruleset = self.recurrence_set.to_rruleset()
        self.assertEqual(len(rruleset._rrule), 1)
        self.assertEqual(len(rruleset._rdate), 1)
