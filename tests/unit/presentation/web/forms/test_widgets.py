import pytest
from wtforms import Form

from project.presentation.web.forms.widgets import CustomDateField


def _field(**kwargs):
    class DateForm(Form):
        date = CustomDateField(**kwargs)

    return DateForm().date


def test_custom_date_field_parses_date_in_berlin():
    field = _field()
    field.process_formdata(["2040-04-01"])
    assert field.data.isoformat() == "2040-04-01T00:00:00+02:00"


def test_custom_date_field_set_end_of_day():
    field = _field(set_end_of_day=True)
    field.process_formdata(["2040-04-01"])
    assert (field.data.hour, field.data.minute) == (23, 59)


def test_custom_date_field_empty_value_clears_data():
    field = _field()
    field.process_formdata([""])
    assert field.data is None


def test_custom_date_field_invalid_value():
    field = _field()
    with pytest.raises(ValueError):
        field.process_formdata(["not-a-date"])
