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
