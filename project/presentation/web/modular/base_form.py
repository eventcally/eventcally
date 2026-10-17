from flask import request
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import FormField, HiddenField, SubmitField

from project.application.query_bus import QueryBus
from project.domain.models.entities.actor import Actor
from project.presentation.web.modular.fields import VirtualFormField


class BlankFormData:
    """Stand-in for an empty object behind a sub-form: every field reads as unset,
    like a fresh model instance (whose attributes are all `None`)."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)

        return None


class BaseForm(FlaskForm):
    def get_current_actor(self) -> Actor:
        from flask import current_app

        return current_app.container.context.context_provider().current_actor

    def get_query_bus(self) -> QueryBus:
        from flask import current_app

        return current_app.container.cqrs.query_bus()

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

    def has_data(self):
        return self.is_submitted()

    def get_field_by_name(self, name: str):
        for field in self.get_input_fields():
            if field.name == name:
                return field

            if isinstance(field, FormField) and isinstance(
                field.form, BaseForm
            ):  # pragma: no cover
                form_result = field.form.get_field_by_name(name)
                if form_result:
                    return form_result

        return None  # pragma: no cover

    def move_field_to_top(self, key: str):
        self._fields.move_to_end(key, False)

    def handle_bff_ajax_validation(self, object, field, **kwargs):
        field.validate(self)

        if field.errors:
            return ". ".join([str(e) for e in field.errors])

        method = getattr(self, f"ajax_validate_{field.name}", None)
        if callable(method):
            return method(object, field, **kwargs)

        return True  # pragma: no cover

    def process(self, formdata=None, obj=None, data=None, extra_filters=None, **kwargs):
        for name, field in self._fields.items():
            if isinstance(field, VirtualFormField):
                kwargs.setdefault(name, obj)

        super().process(formdata, obj, data, extra_filters, **kwargs)


class BaseCreateForm(BaseForm):
    submit = SubmitField(lazy_gettext("Create"))


class BaseUpdateForm(BaseForm):
    submit = SubmitField(lazy_gettext("Update"))


class BaseDeleteForm(BaseForm):
    confirmation_field_name = None
    submit = SubmitField(lazy_gettext("Delete"), render_kw={"class": "btn btn-danger"})


class BaseListForm(BaseForm):
    class Meta:
        csrf = False

    filters = None
    search_definitions = None
    sort_definitions = None

    submit = SubmitField(
        lazy_gettext("Refresh"), render_kw={"class": "btn btn-primary"}
    )

    def is_submitted(self):  # pragma: no cover
        return super().is_submitted() or "submit" in request.args
