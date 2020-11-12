from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired
from project.forms.common import event_rating_choices

class CreateEventReferenceForm(FlaskForm):
    admin_unit_id = SelectField(lazy_gettext('Admin unit'), validators=[DataRequired()], coerce=int)
    rating = SelectField(lazy_gettext('Rating'), default=50, coerce=int, choices=event_rating_choices)
    submit = SubmitField(lazy_gettext("Save reference"))

class UpdateEventReferenceForm(FlaskForm):
    rating = SelectField(lazy_gettext('Rating'), default=50, coerce=int, choices=event_rating_choices)
    submit = SubmitField(lazy_gettext("Update reference"))

class DeleteReferenceForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete reference"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])