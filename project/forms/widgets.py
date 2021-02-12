from datetime import datetime

from flask_babelex import gettext, to_user_timezone
from markupsafe import Markup
from wtforms import DateTimeField, SelectField, SelectMultipleField
from wtforms.validators import StopValidation
from wtforms.widgets import CheckboxInput, ListWidget, html_params

from project.dateutils import berlin_tz


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


def create_option_string(count, value):
    result = ""
    for i in range(count):
        selected = " selected" if i == value else ""
        result = result + '<option value="%02d"%s>%02d</option>' % (i, selected, i)
    return result


class CustomDateTimeWidget:
    def __call__(self, field, **kwargs):
        id = kwargs.pop("id", field.id)
        date = ""
        hour = minute = 0
        if field.data:
            date_value = to_user_timezone(field.data)
            date = date_value.strftime("%Y-%m-%d")
            hour = date_value.hour
            minute = date_value.minute

        kwargs_class = kwargs.pop("class", "")

        date_class = kwargs_class + " datepicker"
        date_params = html_params(
            name=field.name,
            id=id,
            value=date,
            required=field.flags.required,
            class_=date_class,
            **kwargs
        )
        time_hour_params = html_params(
            name=field.name, id=id + "-hour", class_=kwargs_class, **kwargs
        )
        time_minute_params = html_params(
            name=field.name, id=id + "-minute", class_=kwargs_class, **kwargs
        )
        clear_button_id = id + "-clear-button"

        return Markup(
            '<div class="input-group-prepend mt-1"><input type="text" {}/><button class="btn btn-outline-secondary" type="button" id="{}"><i class="fa fa-times"></i></button></div><div class="mx-2"></div><div class="input-group-append mt-1"><select {}>{}</select><span class="input-group-text">:</span><select {}>{}</select></div>'.format(
                date_params,
                clear_button_id,
                time_hour_params,
                create_option_string(24, hour),
                time_minute_params,
                create_option_string(60, minute),
            )
        )


class CustomDateTimeField(DateTimeField):
    widget = CustomDateTimeWidget()

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                date_str, hour_str, minute_str = valuelist
                if not date_str:
                    self.data = None
                    return

                date = datetime.strptime(date_str, "%Y-%m-%d")
                date_time = datetime(
                    date.year, date.month, date.day, int(hour_str), int(minute_str)
                )
                self.data = berlin_tz.localize(date_time)
            except Exception:
                raise ValueError(
                    "Not a valid datetime value. Looking for YYYY-MM-DD HH:mm."
                )


class CustomDateWidget:
    def __call__(self, field, **kwargs):
        id = kwargs.pop("id", field.id)
        date = ""
        if field.data:
            date_value = to_user_timezone(field.data)
            date = date_value.strftime("%Y-%m-%d")

        date_params = html_params(name=field.name, id=id, value=date, **kwargs)
        return Markup('<input type="text" {}/>'.format(date_params))


class CustomDateField(DateTimeField):
    widget = CustomDateWidget()

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                date_str = valuelist[0]
                if not date_str:
                    self.data = None
                    return

                date = datetime.strptime(date_str, "%Y-%m-%d")
                self.data = berlin_tz.localize(date)
            except Exception:
                raise ValueError("Not a valid date value. Looking for YYYY-MM-DD.")


def try_to_int(value):
    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.isdigit():
        try:
            return int(value)
        except ValueError:
            return value

    return value


class TagSelectField(SelectField):
    def __init__(
        self,
        label=None,
        validators=None,
        coerce=try_to_int,
        choices=None,
        validate_choice=True,
        **kwargs
    ):
        super(TagSelectField, self).__init__(
            label, validators, coerce, choices, validate_choice, **kwargs
        )

    def pre_validate(self, form):
        if self.is_free_text():
            if not self.data or not self.data.strip():
                raise StopValidation(gettext("This field is required."))
        else:
            super(TagSelectField, self).pre_validate(form)

    def is_free_text(self):
        return isinstance(self.data, str)
