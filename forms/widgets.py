from wtforms import DateTimeField
from wtforms.widgets import html_params, HTMLString
import pytz
from datetime import datetime

def create_option_string(count, value):
    result = ""
    for i in range(count):
        selected = " selected" if i == value else ""
        result = result + '<option value="%02d"%s>%02d</option>' % (i, selected, i)
    return result

berlin_tz = pytz.timezone('Europe/Berlin')

class CustomDateTimeWidget:
    def __call__(self, field, **kwargs):
        id = kwargs.pop('id', field.id)
        date = ''
        hour = minute = 0
        if field.data:
            date = field.data.strftime("%Y-%m-%d")
            hour = field.data.hour
            minute = field.data.minute

        date_user_kwargs = dict(kwargs)
        date_user_kwargs['class'] = kwargs['class'] + " datepicker"
        date_user_kwargs['autocomplete'] = "off"

        date_hidden_params = html_params(name=field.name, id=id + '-date-hidden', value=date, **kwargs)
        date_user_params = html_params(name="", id=id + '-date', value=date, **date_user_kwargs)
        time_hour_params = html_params(name=field.name, id=id + '-hour', **kwargs)
        time_minute_params = html_params(name=field.name, id=id + '-minute', **kwargs)
        clear_button_id = id + '-clear-button'
        return HTMLString('<input type="hidden" {}/><div class="input-group-prepend mt-1"><input type="text" {}/><button class="btn btn-outline-secondary" type="button" id="{}"><i class="fa fa-times"></i></button></div><div class="mx-2"></div><div class="input-group-append mt-1"><select {}>{}</select><span class="input-group-text">:</span><select {}>{}</select></div>'.format(date_hidden_params, date_user_params, clear_button_id, time_hour_params, create_option_string(24, hour), time_minute_params, create_option_string(60, minute)))

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
                date_time = datetime(date.year, date.month, date.day, int(hour_str), int(minute_str))
                self.data = berlin_tz.localize(date_time)
            except:
                raise ValueError('Not a valid datetime value. Looking for YYYY-MM-DD HH:mm.')
