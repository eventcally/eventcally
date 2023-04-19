from datetime import datetime

from flask_babel import gettext, to_user_timezone
from markupsafe import Markup
from wtforms import DateTimeField, SelectField, SelectMultipleField
from wtforms.fields import StringField
from wtforms.validators import Length, StopValidation
from wtforms.widgets import CheckboxInput, ListWidget, html_params

from project.dateutils import berlin_tz, date_set_end_of_day


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class CustomDateTimeWidget:
    def __call__(self, field, **kwargs):
        id = kwargs.pop("id", field.id)
        date = ""
        time = ""
        if field.data:
            date_value = to_user_timezone(field.data)
            date = date_value.strftime("%Y-%m-%d")
            time = date_value.strftime("%H:%M")

        kwargs_class = kwargs.pop("class", "")
        required = True if field.flags.required else False

        date_class = kwargs_class + " datepicker"
        date_params = html_params(
            name=field.name,
            id=id,
            value=date,
            required=required,
            class_=date_class,
            **kwargs
        )

        time_class = kwargs_class + " timepicker"
        time_params = html_params(
            name=field.name,
            id=id + "-time",
            value=time,
            required=required,
            class_=time_class,
            **kwargs
        )

        return Markup(
            '<div class="input-group-prepend mt-1"><input type="text" {}/></div><div class="mx-2"></div><div class="input-group-append mt-1"><input {} /></div>'.format(
                date_params,
                time_params,
            )
        )


class CustomDateTimeField(DateTimeField):
    widget = CustomDateTimeWidget()

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                date_str, time_str = valuelist
                if not date_str:
                    self.data = None
                    return

                date_time_str = date_str + " " + time_str
                date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
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
    set_end_of_day = False
    widget = CustomDateWidget()

    def __init__(
        self,
        label=None,
        validators=None,
        format="%Y-%m-%d %H:%M:%S",
        set_end_of_day=False,
        **kwargs
    ):
        super(CustomDateField, self).__init__(label, validators, format, **kwargs)
        self.set_end_of_day = set_end_of_day

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                date_str = valuelist[0]
                if not date_str:
                    self.data = None
                    return

                date = datetime.strptime(date_str, "%Y-%m-%d")
                localized_date = berlin_tz.localize(date)

                if self.set_end_of_day:
                    localized_date = date_set_end_of_day(localized_date)

                self.data = localized_date
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


class HTML5StringField(StringField):
    def __init__(
        self,
        label=None,
        validators=None,
        filters=(),
        description="",
        id=None,
        default=None,
        widget=None,
        render_kw=None,
        name=None,
        _form=None,
        _prefix="",
        _translations=None,
        _meta=None,
    ):
        for validator in validators:
            if isinstance(validator, Length):
                if not render_kw:
                    render_kw = {}
                if validator.max > 0:
                    render_kw["maxlength"] = validator.max
                if validator.min > 0:
                    render_kw["minlength"] = validator.min

        super().__init__(
            label,
            validators,
            filters,
            description,
            id,
            default,
            widget,
            render_kw,
            name,
            _form,
            _prefix,
            _translations,
            _meta,
        )
