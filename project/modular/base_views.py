from flask import flash, jsonify, redirect, render_template, request
from flask.views import View
from flask_babel import lazy_gettext
from sqlalchemy.exc import SQLAlchemyError
from wtforms import RadioField, SelectField, StringField

from project import db
from project.modular.filters import BooleanFilter, EnumFilter
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handle_db_error,
    handleSqlError,
)


class BaseView(View):
    template_file_name = None

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.handler = kwargs.get("handler")
        self.decorators.extend(self.handler.decorators)

    @property
    def model(self):
        return self.handler.model

    def get_title(self, **kwargs):  # pragma: no cover
        return ""

    def get_instruction(self, **kwargs):  # pragma: no cover
        return ""

    def get_docs_url(self, **kwargs):  # pragma: no cover
        return None

    def get_templates(self):
        result = list()

        for path in self.handler.template_pathes:
            result.append(
                f"{path}{self.handler.get_template_folder()}/{self.template_file_name}"
            )
            result.append(f"{path}generic/{self.template_file_name}")

        return result

    def check_access(self, **kwargs):
        return self.handler.check_access(**kwargs)

    def handle_backend_for_frontend(self, object=None, form=None, **kwargs):
        return None

    def render_template(self, **kwargs):
        kwargs.setdefault("title", self.get_title(**kwargs))
        kwargs.setdefault("instruction", self.get_instruction(**kwargs))
        kwargs.setdefault("view", self)
        return render_template(self.get_templates(), **kwargs)

    def get_breadcrumbs(self):
        return self.handler.get_breadcrumbs()

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        return self.render_template(**kwargs)


class BaseListView(BaseView):
    display_class = None
    list_context_name = None
    template_file_name = "list.html"
    form_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.list_context_name and self.model:
            self.list_context_name = f"{self.model.__model_name_plural__}"

    def create_display(self, **kwargs):
        return self.display_class(**kwargs)

    def create_form(self, **kwargs):
        if not self.form_class:
            return None

        class ListForm(self.form_class):
            pass

        if self.form_class.search_definitions:
            field = self.create_search_field()
            setattr(ListForm, "keyword", field)

        for filter in self.form_class.filters:
            field = self.create_field_for_filter(filter)
            setattr(ListForm, filter.key, field)

        if self.form_class.sort_definitions:
            field = self.create_sort_field(self.form_class.sort_definitions)
            setattr(ListForm, "sort", field)

        form = ListForm(**kwargs)
        return form

    def create_field_for_filter(self, filter):
        if isinstance(filter, BooleanFilter):
            field = RadioField(
                filter.label,
                choices=filter.options,
                default="",
                coerce=str,
                render_kw={"formrow": True, "ri": "radio"},
            )
        elif isinstance(filter, EnumFilter):
            field = SelectField(
                filter.label,
                choices=filter.options,
                default="",
                coerce=int,
                render_kw={"formrow": True},
            )
        else:
            raise NotImplementedError()  # pragma: no cover

        return field

    def create_search_field(self):
        field = StringField(lazy_gettext("Keyword"), render_kw={"formrow": True})
        return field

    def create_sort_field(self, definitions):
        choices = list()

        for definition in definitions:
            choices.append((definition.key, definition.label))

        default = choices[0][0]

        field = SelectField(
            lazy_gettext("Sort"),
            render_kw={"formrow": True},
            choices=choices,
            default=default,
        )
        return field

    def get_title(self, **kwargs):
        return self.handler.get_model_display_name_plural()

    def get_objects_query_from_kwargs(self, **kwargs):
        return self.handler.get_objects_query_from_kwargs(**kwargs)

    def render_template(self, **kwargs):
        if "objects" in kwargs and self.list_context_name:
            kwargs[self.list_context_name] = kwargs.get("objects")
        return super().render_template(**kwargs)

    def get_list_per_page(self):
        return self.handler.get_list_per_page()

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        form = self.create_form(formdata=request.args)
        query = self.get_objects_query_from_kwargs(form=form, **kwargs)
        paginate = query.paginate(per_page=self.get_list_per_page())
        objects = paginate.items
        pagination = get_pagination_urls(paginate, **kwargs)
        display = self.create_display()

        return self.render_template(
            display=display, form=form, objects=objects, pagination=pagination
        )


class BaseObjectView(BaseView):
    object_context_name = None
    display_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.object_context_name and self.model:
            self.object_context_name = f"{self.model.__model_name__}"

    def get_object_from_kwargs(self, **kwargs):
        return self.handler.get_object_from_kwargs(**kwargs)

    def check_object_access(self, object):
        return self.handler.check_object_access(object)

    def create_display(self, **kwargs):
        return self.display_class(**kwargs)

    def render_template(self, **kwargs):
        object = kwargs.get("object")
        if object and self.object_context_name:
            kwargs[self.object_context_name] = object

        if self.display_class:
            kwargs["display"] = self.create_display()

        return super().render_template(**kwargs)

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()

        list_url = self.handler.get_list_url()
        if list_url:
            result.append(
                self.handler._create_breadcrumb(
                    list_url, self.handler.get_model_display_name_plural()
                )
            )

        return result


class BaseFormView(BaseObjectView):
    methods = ["GET", "POST"]
    form_class = None

    def create_form(self, **kwargs):
        return self.form_class(**kwargs)

    def create_object(self):
        return self.model()

    def complete_object(self, object, form):
        self.handler.complete_object(object, form)

    def handle_backend_for_frontend(self, object=None, form=None, **kwargs):
        response = super().handle_backend_for_frontend(object, form, **kwargs)

        if response:  # pragma: no cover
            return response

        bff_header = request.headers.get("X-Backend-For-Frontend")
        if bff_header:
            method = getattr(self, f"handle_bff_{bff_header}", None)
            if callable(method):
                field_name = request.args.get("field_name")
                field = form.get_field_by_name(field_name)
                return jsonify(method(object, form, field, **kwargs))

        return None

    def handle_bff_ajax_lookup(self, object, form, field, **kwargs):
        return field.loader.get_ajax_pagination(request.args.get("term"))

    def handle_bff_ajax_validation(self, object, form, field, **kwargs):
        if form:
            return form.handle_bff_ajax_validation(object, field, **kwargs)
        return True  # pragma: no cover

    def handle_bff_google_places(self, object, form, field, **kwargs):
        return field.get_bff_google_places(request.args.get("keyword"))

    def handle_bff_google_place(self, object, form, field, **kwargs):
        return field.get_bff_google_place(request.args.get("gmaps_id"))

    def after_commit(self, object, form):
        pass

    def get_redirect_url(self, **kwargs):  # pragma: no cover
        return None

    def get_success_text(self, object, form):  # pragma: no cover
        return ""


class BaseReadView(BaseObjectView):
    template_file_name = "read.html"

    def get_title(self, **kwargs):
        return str(kwargs["object"])

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:  # pragma: no cover
            return response

        return self.render_template(object=object)


class BaseCreateView(BaseFormView):
    template_file_name = "create.html"

    def get_redirect_url(self, **kwargs):
        result = self.handler.get_read_url(**kwargs)

        if not result:
            result = self.handler.get_list_url(**kwargs)

        return result

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Create %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )

    def get_success_text(self, object, form):
        return lazy_gettext(
            "%(model_display_name)s successfully created",
            model_display_name=self.handler.get_model_display_name(),
        )

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        form = self.create_form()
        object = None

        response = self.handle_backend_for_frontend(object, form, **kwargs)

        if response:
            return response

        if form.validate_on_submit():
            object = self.create_object()
            form.populate_obj(object)

            try:
                self.complete_object(object, form)
                db.session.add(object)
                db.session.commit()
                self.after_commit(object, form)
                flash(self.get_success_text(object, form), "success")
                return redirect(self.get_redirect_url(object=object))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
        else:
            flash_errors(form)

        return self.render_template(form=form, object=object)


class BaseObjectFormView(BaseFormView):
    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:  # pragma: no cover
            return response

        form = self.create_form(obj=object)

        response = self.handle_backend_for_frontend(object, form, **kwargs)

        if response:  # pragma: no cover
            return response

        if form.validate_on_submit():
            response = self.dispatch_validated_form(form, object, **kwargs)
            if response:
                return response
        else:
            flash_errors(form)

        return self.render_template(form=form, object=object)

    def dispatch_validated_form(self, form, object, **kwargs):  # pragma: no cover
        raise NotImplementedError()


class BaseUpdateView(BaseObjectFormView):
    template_file_name = "update.html"

    def get_redirect_url(self, **kwargs):
        result = self.handler.get_read_url(**kwargs)

        if not result:
            result = self.handler.get_list_url(**kwargs)

        return result

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Update %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )

    def get_success_text(self, object, form):
        return lazy_gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=self.handler.get_model_display_name(),
        )

    def dispatch_validated_form(self, form, object, **kwargs):
        form.populate_obj(object)

        try:
            self.complete_object(object, form)
            db.session.commit()
            self.after_commit(object, form)
            flash(self.get_success_text(object, form), "success")
            return redirect(self.get_redirect_url(object=object))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")


class BaseDeleteView(BaseObjectFormView):
    template_file_name = "delete.html"

    def can_object_be_deleted(self, form, object):
        return self.handler.can_object_be_deleted(form, object)

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Delete %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "Do you want to delete '%(object_title)s'?",
            object_title=str(kwargs["object"]),
        )

    def get_success_text(self, object, form):
        return lazy_gettext(
            "%(model_display_name)s successfully deleted",
            model_display_name=self.handler.get_model_display_name(),
        )

    def create_form(self, **kwargs):
        del kwargs["obj"]
        return self.form_class(**kwargs)

    def delete_object_from_db(self, object):
        db.session.delete(object)
        db.session.commit()

    def flash_success_text(self, form, object):
        flash(self.get_success_text(object, form), "success")

    @handle_db_error
    def dispatch_validated_form(self, form, object, **kwargs):
        if self.can_object_be_deleted(form, object):
            self.delete_object_from_db(object)
            self.after_commit(object, form)
            self.flash_success_text(form, object)
            return redirect(self.get_redirect_url())
