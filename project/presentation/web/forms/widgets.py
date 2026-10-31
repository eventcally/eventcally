from datetime import datetime

from flask_babel import to_user_timezone
from markupsafe import Markup
from wtforms import DateTimeField, SelectMultipleField
from wtforms.widgets import CheckboxInput, ListWidget, html_params

from project.shared.dateutils import berlin_tz, date_set_end_of_day


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


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
        **kwargs,
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

                date_str_p = date_str.split(" ")[0].split("T")[0]
                date = datetime.strptime(date_str_p, "%Y-%m-%d")
                localized_date = date.replace(tzinfo=berlin_tz)

                if self.set_end_of_day:
                    localized_date = date_set_end_of_day(localized_date)

                self.data = localized_date
            except Exception:
                raise ValueError("Not a valid date value. Looking for YYYY-MM-DD.")
