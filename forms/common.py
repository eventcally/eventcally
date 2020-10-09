from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Optional

class BaseImageForm(FlaskForm):
    image_file = FileField(lazy_gettext('File'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])
    copyright_text = StringField(lazy_gettext('Copyright text'), validators=[Optional()])
    delete_flag = BooleanField(lazy_gettext('Delete image'), default=False, validators=[Optional()])

    def populate_obj(self, obj):
        super(FlaskForm, self).populate_obj(obj)

        if self.image_file.data:
            fs = self.image_file.data
            obj.data = fs.read()
            obj.encoding_format = fs.content_type
        elif self.delete_flag.data:
            obj.data = None

event_rating_choices = [
            (0,lazy_gettext('0 (Little relevant)')),
            (10,'1'),
            (20,'2'),
            (30,'3'),
            (40,'4'),
            (50,'5'),
            (60,'6'),
            (70,'7'),
            (80,'8'),
            (90,'9'),
            (100,lazy_gettext('10 (Highlight)'))
        ]

weekday_choices = [
            (1,lazy_gettext('Monday')),
            (2,lazy_gettext('Tueday')),
            (3,lazy_gettext('Wednesday')),
            (4,lazy_gettext('Thursday')),
            (5,lazy_gettext('Friday')),
            (6,lazy_gettext('Saturday')),
            (0,lazy_gettext('Sunday'))
        ]

distance_choices = [
            (500,lazy_gettext('500 m')),
            (5000,lazy_gettext('5 km')),
            (10000,lazy_gettext('10 km')),
            (25000,lazy_gettext('20 km')),
            (50000,lazy_gettext('50 km')),
            (100000,lazy_gettext('100 km'))
        ]
