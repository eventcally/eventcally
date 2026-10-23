from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import Optional

from project.presentation.web.forms.widgets import CustomDateField


class FindEventDateBaseForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    keyword = StringField(lazy_gettext("Keyword"), validators=[Optional()])
    category_id = SelectField(
        lazy_gettext("Category"), validators=[Optional()], coerce=int
    )
    tag = StringField(lazy_gettext("Tags"), validators=[Optional()])


class FindEventDateWidgetForm(FindEventDateBaseForm):
    s_ft = HiddenField(validators=[Optional()])
    s_bg = HiddenField(validators=[Optional()])
    s_pr = HiddenField(validators=[Optional()])
    s_li = HiddenField(validators=[Optional()])

    submit = SubmitField(lazy_gettext("Find"))
