from flask import jsonify
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField


class BaseForm(FlaskForm):
    def get_input_fields(self):
        return list(
            filter(
                lambda field: not isinstance(field, HiddenField)
                and not isinstance(field, SubmitField),
                self.__iter__(),
            )
        )

    def get_button_fields(self):
        return list(
            filter(
                lambda field: isinstance(field, SubmitField),
                self.__iter__(),
            )
        )

    def move_field_to_top(self, key: str):
        self._fields.move_to_end(key, False)

    def handle_ajax_validation(self, object, field, **kwargs):
        method = getattr(self, f"ajax_validate_{field.name}", None)
        if callable(method):
            return jsonify(method(object, field, **kwargs))

        return jsonify(True)  # pragma: no cover


class BaseCreateForm(BaseForm):
    submit = SubmitField(lazy_gettext("Create"))


class BaseUpdateForm(BaseForm):
    submit = SubmitField(lazy_gettext("Update"))


class BaseDeleteForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete"))
