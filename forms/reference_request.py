from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired
from .common import event_rating_choices

class CreateEventReferenceRequestForm(FlaskForm):
    admin_unit_id = SelectField(lazy_gettext('Admin unit'), validators=[DataRequired()], coerce=int)
    submit = SubmitField(lazy_gettext("Save request"))

class DeleteReferenceRequestForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete request"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])