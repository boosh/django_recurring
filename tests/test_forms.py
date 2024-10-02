import json
from datetime import datetime, timedelta

import pytest
import pytz
from recurring.forms import CalendarEntryForm
from recurring.models import CalendarEntry, Timezone


@pytest.fixture
def timezone_obj():
    return Timezone.objects.get_or_create(name="UTC")[0]


@pytest.fixture
def valid_calendar_entry_data():
    """Fixture to provide valid calendar entry data."""
    return {
        "name": "Test Calendar Entry",
        "description": "A test calendar entry",
        "timezone": 1,
        "calendar_entry": json.dumps(
            {
                "events": [
                    {
                        "start_time": "2023-01-01T00:00:00",
                        "end_time": "2023-01-01T01:00:00",
                        "is_full_day": False,
                        "rule": {"frequency": "DAILY", "interval": 1},
                        "exclusions": [],
                    }
                ]
            }
        ),
    }


@pytest.mark.django_db
class TestCalendarEntryForm:
    def test_form_valid_data(self, valid_calendar_entry_data):
        """Test that the form is valid with correct data."""
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert form.is_valid(), form.errors

    def test_form_missing_required_fields(self):
        """Test that the form is invalid when required fields are missing."""
        form = CalendarEntryForm(data={})
        assert not form.is_valid()
        assert "timezone" in form.errors

    def test_form_invalid_json(self, valid_calendar_entry_data):
        """Test that the form is invalid when calendar_entry JSON is malformed."""
        valid_calendar_entry_data["calendar_entry"] = "invalid json"
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert not form.is_valid()
        assert "calendar_entry" in form.errors

    def test_form_missing_events(self, valid_calendar_entry_data):
        """Test that the form is invalid when events are missing."""
        data = json.loads(valid_calendar_entry_data["calendar_entry"])
        data["events"] = []
        valid_calendar_entry_data["calendar_entry"] = json.dumps(data)
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert not form.is_valid()
        assert any(
            "You must add at least one event" in error
            for error in form.non_field_errors()
        )

    def test_form_invalid_event_structure(self, valid_calendar_entry_data):
        """Test that the form is invalid when event structure is incorrect."""
        data = json.loads(valid_calendar_entry_data["calendar_entry"])
        data["events"][0].pop("start_time")
        valid_calendar_entry_data["calendar_entry"] = json.dumps(data)
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert not form.is_valid()
        assert "calendar_entry" in form.errors

    def test_form_invalid_exclusion(self, valid_calendar_entry_data):
        """Test that the form is invalid when exclusion is incorrect."""
        data = json.loads(valid_calendar_entry_data["calendar_entry"])
        data["events"][0]["exclusions"] = [
            {"start_date": "2023-01-01"}
        ]  # Missing end_date
        valid_calendar_entry_data["calendar_entry"] = json.dumps(data)
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert not form.is_valid()
        assert "calendar_entry" in form.errors

    def test_form_save_method(self, valid_calendar_entry_data):
        """Test that the form save method creates a CalendarEntry instance."""
        form = CalendarEntryForm(data=valid_calendar_entry_data)
        assert form.is_valid(), form.errors
        instance = form.save()
        assert isinstance(instance, CalendarEntry)
        assert instance.pk is not None
        assert instance.name == valid_calendar_entry_data["name"]
        assert instance.description == valid_calendar_entry_data["description"]
        assert instance.timezone.id == valid_calendar_entry_data["timezone"]
        assert instance.events.count() == 1

    def test_form_update_existing_instance(
        self, valid_calendar_entry_data, timezone_obj
    ):
        """Test that the form updates an existing CalendarEntry instance."""
        initial_instance = CalendarEntry.objects.create(
            name="Initial Name",
            description="Initial Description",
            timezone=timezone_obj,
        )
        form = CalendarEntryForm(
            data=valid_calendar_entry_data, instance=initial_instance
        )
        assert form.is_valid(), form.errors
        updated_instance = form.save()
        assert updated_instance.pk == initial_instance.pk
        assert updated_instance.name == valid_calendar_entry_data["name"]
        assert updated_instance.description == valid_calendar_entry_data["description"]
        assert updated_instance.timezone.id == valid_calendar_entry_data["timezone"]

    def test_form_initial_data_population(self, timezone_obj):
        """Test that the form is correctly populated with initial data from an existing instance."""
        existing_instance = CalendarEntry.objects.create(
            name="Existing Entry",
            description="An existing calendar entry",
            timezone=timezone_obj,
        )
        existing_instance.from_dict(
            {
                "events": [
                    {
                        "start_time": datetime.now(pytz.UTC),
                        "end_time": datetime.now(pytz.UTC) + timedelta(hours=1),
                        "is_full_day": False,
                        "rule": {"frequency": "DAILY", "interval": 1},
                        "exclusions": [],
                    }
                ]
            }
        )
        form = CalendarEntryForm(instance=existing_instance)
        assert form.initial["name"] == "Existing Entry"
        assert form.initial["description"] == "An existing calendar entry"
        assert form.initial["timezone"] == timezone_obj.id
        assert "calendar_entry" in form.initial
        assert isinstance(json.loads(form.initial["calendar_entry"]), dict)

    def test_form_widget_attributes(self):
        """Test that the form widget has the correct attributes."""
        form = CalendarEntryForm()
        widget = form.fields["calendar_entry"].widget
        assert widget.__class__.__name__ == "CalendarEntryWidget"
        assert widget.attrs["style"] == "display: none;"

    @pytest.mark.parametrize(
        "invalid_field,invalid_value",
        [
            ("timezone", "Invalid/Timezone"),  # Invalid timezone
            (
                "calendar_entry",
                '{"invalid": "json"}',
            ),  # Invalid calendar entry structure
        ],
    )
    def test_form_field_validation(
        self, valid_calendar_entry_data, invalid_field, invalid_value
    ):
        """Test validation for individual fields with invalid data."""
        invalid_data = valid_calendar_entry_data.copy()
        invalid_data[invalid_field] = invalid_value
        form = CalendarEntryForm(data=invalid_data)
        assert not form.is_valid()
        assert invalid_field in form.errors
