from flask import flash, redirect, render_template
from flask.views import View
from flask_babel import lazy_gettext
from sqlalchemy.exc import SQLAlchemyError

from project import db
from project.views.utils import flash_errors, get_pagination_urls, handleSqlError


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

    def render_template(self, **kwargs):
        kwargs.setdefault("title", self.get_title(**kwargs))
        kwargs.setdefault("instruction", self.get_instruction(**kwargs))
        kwargs.setdefault("view", self)
        return render_template(self.get_templates(), **kwargs)

    def get_breadcrumbs(self):
        return self.handler.get_breadcrumbs()


class BaseListView(BaseView):
    display_class = None
    list_context_name = None
    template_file_name = "list.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.list_context_name and self.model:
            self.list_context_name = f"{self.model.__model_name_plural__}"

    def create_display(self, **kwargs):
        return self.display_class(**kwargs)

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

        query = self.get_objects_query_from_kwargs(**kwargs)
        paginate = query.paginate(per_page=self.get_list_per_page())
        objects = paginate.items
        pagination = get_pagination_urls(paginate, **kwargs)
        display = self.create_display()
        return self.render_template(
            display=display, objects=objects, pagination=pagination
        )


class BaseObjectView(BaseView):
    object_context_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.object_context_name and self.model:
            self.object_context_name = f"{self.model.__model_name__}"

    def get_object_from_kwargs(self, **kwargs):
        return self.model.query.get_or_404(
            kwargs.get(self.handler.get_id_query_arg_name())
        )

    def check_object_access(self, object):
        return self.handler.check_object_access(object)

    def render_template(self, **kwargs):
        object = kwargs.get("object")
        if object and self.object_context_name:
            kwargs[self.object_context_name] = object
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

    def after_commit(self, object, form):
        pass

    def get_redirect_url(self, **kwargs):  # pragma: no cover
        return None

    def get_success_text(self, object, form):  # pragma: no cover
        return ""


class BaseReadView(BaseObjectView):
    display_class = None
    template_file_name = "read.html"

    def create_display(self, **kwargs):
        return self.display_class(**kwargs)

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

        display = self.create_display()
        return self.render_template(display=display, object=object)


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


class BaseUpdateView(BaseFormView):
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

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:
            return response

        form = self.create_form(obj=object)

        if form.validate_on_submit():
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
        else:
            flash_errors(form)

        return self.render_template(form=form, object=object)


class BaseDeleteView(BaseFormView):
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

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:  # pragma: no cover
            return response

        form = self.create_form()

        if form.validate_on_submit():
            if self.can_object_be_deleted(form, object):
                try:
                    db.session.delete(object)
                    db.session.commit()
                    self.after_commit(object, form)
                    flash(self.get_success_text(object, form), "success")
                    return redirect(self.get_redirect_url())
                except SQLAlchemyError as e:
                    db.session.rollback()
                    flash(handleSqlError(e), "danger")
        else:
            flash_errors(form)

        return self.render_template(form=form, object=object)
