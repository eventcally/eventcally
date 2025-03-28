from datetime import datetime

from flask_babel import to_user_timezone
from markupsafe import Markup
from wtforms import DateTimeField, SelectMultipleField
from wtforms.fields import StringField
from wtforms.validators import Length
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
            **kwargs,
        )

        time_class = kwargs_class + " timepicker"
        time_params = html_params(
            name=field.name,
            id=id + "-time",
            value=time,
            required=required,
            class_=time_class,
            **kwargs,
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

        html = []
        html.append('<input type="text" {}/>'.format(date_params))

        if field.clearable:
            html.append("<div %s>" % html_params(class_="input-group-append"))
            html.append(
                f'<button class="btn btn-outline-secondary" type="button" data-role="clear-datepicker-btn" data-target="#{id}">'
            )
            html.append('<i class="fa fa-times"></i>')
            html.append("</div>")

        return Markup("".join(html))


class CustomDateField(DateTimeField):
    set_end_of_day = False
    widget = CustomDateWidget()

    def __init__(
        self,
        label=None,
        validators=None,
        format="%Y-%m-%d %H:%M:%S",
        set_end_of_day=False,
        clearable=False,
        **kwargs,
    ):
        super(CustomDateField, self).__init__(label, validators, format, **kwargs)
        self.set_end_of_day = set_end_of_day
        self.clearable = clearable

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                date_str = valuelist[0]
                if not date_str:
                    self.data = None
                    return

                date_str_p = date_str.split(" ")[0].split("T")[0]
                date = datetime.strptime(date_str_p, "%Y-%m-%d")
                localized_date = berlin_tz.localize(date)

                if self.set_end_of_day:
                    localized_date = date_set_end_of_day(localized_date)

                self.data = localized_date
            except Exception:
                raise ValueError("Not a valid date value. Looking for YYYY-MM-DD.")


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
