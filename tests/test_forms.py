import json
from datetime import datetime, timedelta

import pytest
import pytz

from recurring.forms import RecurrenceSetForm
from recurring.models import RecurrenceSet, Timezone


@pytest.fixture
def timezone_obj():
    return Timezone.objects.get_or_create(name="UTC")[0]


@pytest.fixture
def valid_recurrence_set_data():
    """Fixture to provide valid recurrence set data."""
    return {
        "name": "Test Recurrence Set",
        "description": "A test recurrence set",
        "timezone": 1,
        "recurrence_set": json.dumps(
            {
                "rules": [
                    {
                        "rule": {"frequency": "DAILY", "interval": 1},
                        "dateRanges": [
                            {
                                "startDate": "2023-01-01T00:00:00",
                                "endDate": "2023-12-31T23:59:59",
                            }
                        ],
                    }
                ]
            }
        ),
    }


@pytest.mark.django_db
class TestRecurrenceSetForm:
    def test_form_valid_data(self, valid_recurrence_set_data):
        """Test that the form is valid with correct data."""
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert form.is_valid(), form.errors

    def test_form_missing_required_fields(self):
        """Test that the form is invalid when required fields are missing."""
        form = RecurrenceSetForm(data={})
        assert not form.is_valid()
        assert "timezone" in form.errors

    def test_form_invalid_json(self, valid_recurrence_set_data):
        """Test that the form is invalid when recurrence_set JSON is malformed."""
        valid_recurrence_set_data["recurrence_set"] = "invalid json"
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert not form.is_valid()
        assert "recurrence_set" in form.errors

    def test_form_missing_rules(self, valid_recurrence_set_data):
        """Test that the form is invalid when rules are missing."""
        data = json.loads(valid_recurrence_set_data["recurrence_set"])
        data["rules"] = []
        valid_recurrence_set_data["recurrence_set"] = json.dumps(data)
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert not form.is_valid()
        assert any(
            "You must add at least one rule" in error
            for error in form.non_field_errors()
        )

    def test_form_invalid_rule_structure(self, valid_recurrence_set_data):
        """Test that the form is invalid when rule structure is incorrect."""
        data = json.loads(valid_recurrence_set_data["recurrence_set"])
        data["rules"][0].pop("rule")
        valid_recurrence_set_data["recurrence_set"] = json.dumps(data)
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert not form.is_valid()
        assert "recurrence_set" in form.errors

    def test_form_invalid_date_range(self, valid_recurrence_set_data):
        """Test that the form is invalid when date range is incorrect."""
        data = json.loads(valid_recurrence_set_data["recurrence_set"])
        data["rules"][0]["dateRanges"][0].pop("startDate")
        valid_recurrence_set_data["recurrence_set"] = json.dumps(data)
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert not form.is_valid()
        assert "recurrence_set" in form.errors

    def test_form_save_method(self, valid_recurrence_set_data):
        """Test that the form save method creates a RecurrenceSet instance."""
        form = RecurrenceSetForm(data=valid_recurrence_set_data)
        assert form.is_valid(), form.errors
        instance = form.save()
        assert isinstance(instance, RecurrenceSet)
        assert instance.pk is not None
        assert instance.name == valid_recurrence_set_data["name"]
        assert instance.description == valid_recurrence_set_data["description"]
        assert instance.timezone.id == valid_recurrence_set_data["timezone"]
        assert instance.recurrencesetrules.count() == 1

    def test_form_update_existing_instance(
        self, valid_recurrence_set_data, timezone_obj
    ):
        """Test that the form updates an existing RecurrenceSet instance."""
        initial_instance = RecurrenceSet.objects.create(
            name="Initial Name",
            description="Initial Description",
            timezone=timezone_obj,
        )
        form = RecurrenceSetForm(
            data=valid_recurrence_set_data, instance=initial_instance
        )
        assert form.is_valid(), form.errors
        updated_instance = form.save()
        assert updated_instance.pk == initial_instance.pk
        assert updated_instance.name == valid_recurrence_set_data["name"]
        assert updated_instance.description == valid_recurrence_set_data["description"]
        assert updated_instance.timezone.id == valid_recurrence_set_data["timezone"]

    def test_form_initial_data_population(self, timezone_obj):
        """Test that the form is correctly populated with initial data from an existing instance."""
        existing_instance = RecurrenceSet.objects.create(
            name="Existing Set",
            description="An existing recurrence set",
            timezone=timezone_obj,
        )
        existing_instance.from_dict(
            {
                "rules": [
                    {
                        "rule": {"frequency": "DAILY", "interval": 1},
                        "date_ranges": [
                            {
                                "start_date": datetime.now(pytz.UTC),
                                "end_date": datetime.now(pytz.UTC) + timedelta(days=30),
                            }
                        ],
                    }
                ]
            }
        )
        form = RecurrenceSetForm(instance=existing_instance)
        assert form.initial["name"] == "Existing Set"
        assert form.initial["description"] == "An existing recurrence set"
        assert form.initial["timezone"] == timezone_obj.id
        assert "recurrence_set" in form.initial
        assert isinstance(json.loads(form.initial["recurrence_set"]), dict)

    def test_form_widget_attributes(self):
        """Test that the form widget has the correct attributes."""
        form = RecurrenceSetForm()
        widget = form.fields["recurrence_set"].widget
        assert widget.__class__.__name__ == "RecurrenceSetWidget"
        assert widget.attrs["style"] == "display: none;"

    @pytest.mark.parametrize(
        "invalid_field,invalid_value",
        [
            ("timezone", "Invalid/Timezone"),  # Invalid timezone
            (
                "recurrence_set",
                '{"invalid": "json"}',
            ),  # Invalid recurrence set structure
        ],
    )
    def test_form_field_validation(
        self, valid_recurrence_set_data, invalid_field, invalid_value
    ):
        """Test validation for individual fields with invalid data."""
        invalid_data = valid_recurrence_set_data.copy()
        invalid_data[invalid_field] = invalid_value
        form = RecurrenceSetForm(data=invalid_data)
        assert not form.is_valid()
        assert invalid_field in form.errors
