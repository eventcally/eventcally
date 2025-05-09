from flask import request
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import FormField, HiddenField, SubmitField

from project.modular.fields import VirtualFormField
from project.modular.search_definition import apply_search_definitions


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

    def apply_query_filter(self, query, **kwargs):
        if self.filters:
            for filter in self.filters:
                form_field = getattr(self, filter.key)
                if form_field and form_field.data:
                    query = filter.apply(query, form_field.data, None)

        if self.search_definitions and self.keyword and self.keyword.data:
            query = apply_search_definitions(
                query, self.search_definitions, self.keyword.data
            )

        return query

    def apply_query_order(self, query, **kwargs):
        if self.sort_definitions:
            for definition in self.sort_definitions:
                if self.sort.data == definition.key:
                    return definition.apply(query)

        return query  # pragma: no cover

    def is_submitted(self):  # pragma: no cover
        return super().is_submitted() or "submit" in request.args
