from typing import Optional

from flask import Blueprint, abort, current_app, url_for
from flask_babel import gettext

from project.modular.base_blueprint import BaseBlueprint
from project.modular.base_form import BaseDeleteForm, BaseListForm
from project.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseReadView,
    BaseUpdateView,
    BaseView,
)


class BaseViewHandler:
    decorators = []
    model = None
    object_service = None
    create_view_class = BaseCreateView
    create_form_class = None
    create_decorators = []
    read_view_class = BaseReadView
    read_display_class = None
    read_decorators = []
    update_view_class = BaseUpdateView
    update_form_class = None
    update_display_class = None
    update_decorators = []
    delete_view_class = BaseDeleteView
    delete_form_class = BaseDeleteForm
    delete_decorators = []
    list_view_class = BaseListView
    list_display_class = None
    list_decorators = []
    list_form_class = None
    list_filters = []
    list_search_definitions = []
    list_sort_definitions = []
    generic_prefix = ""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.parent: Optional[BaseViewHandler] = kwargs.get("parent", None)
        self.app = None
        self.endpoints = dict()
        self.template_pathes = list()
        self.permissions = set()

        if not self.list_form_class and (
            self.list_filters
            or self.list_search_definitions
            or self.list_sort_definitions
        ):

            class ListForm(BaseListForm):
                pass

            self.list_form_class = ListForm

    def get_model_display_name(self):
        return self.model.get_display_name()

    def get_model_display_name_plural(self):
        return self.model.get_display_name_plural()

    def get_object_from_kwargs(self, **kwargs):
        object_id = kwargs.get(self.get_id_query_arg_name())
        object = self.get_object_by_id(object_id)

        if not object:  # pragma: no cover
            abort(404)

        return object

    def get_object_by_id(self, object_id):
        return self.object_service.get_object_by_id(object_id)

    def insert_object(self, object):
        self.object_service.insert_object(object)

    def save_object(self, object):
        self.object_service.update_object(object)

    def delete_object(self, object):
        self.object_service.delete_object(object)

    def complete_object(self, object, form):  # pragma: no cover
        pass

    def check_object_access(self, object):  # pragma: no cover
        return None

    def check_access(self, **kwargs):
        return None

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return self.model.query

    def get_objects_query_from_kwargs(self, **kwargs):
        query = self.get_objects_base_query_from_kwargs(**kwargs)
        query = self.apply_base_filter(query, **kwargs)

        form = kwargs.get("form", None)
        if form:
            query = form.apply_query_filter(query, **kwargs)

        query = self.apply_objects_query_order(query, **kwargs)
        return query

    def apply_base_filter(self, query, **kwargs):
        return query

    def apply_objects_query_order(self, query, **kwargs):
        form = kwargs.get("form", None)

        if form:
            return form.apply_query_order(query, **kwargs)

        return query

    def can_object_be_deleted(self, form, object):  # pragma: no cover
        return True

    def get_list_per_page(self):
        return 20

    def get_endpoint_url(self, endpoint_key, **kwargs):
        endpoint = self.endpoints.get(endpoint_key)
        if endpoint:
            if isinstance(self.app, Blueprint):
                blueprint_endpoint = next(
                    (k for k, v in current_app.blueprints.items() if v == self.app),
                    None,
                )
                app_endpoint = f"{blueprint_endpoint}.{endpoint}"
            else:  # pragma: no cover
                app_endpoint = endpoint
            return url_for(app_endpoint, **kwargs)
        return None  # pragma: no cover

    def _get_object_url(self, endpoint_key, object, **kwargs):
        kwargs.setdefault(self.get_id_query_arg_name(), object.id)
        return self.get_endpoint_url(endpoint_key, **kwargs)

    def get_read_url(self, object, **kwargs):
        return self._get_object_url("read", object, **kwargs)

    def get_create_url(self, **kwargs):
        return self.get_endpoint_url("create", **kwargs)

    def get_update_url(self, object, **kwargs):
        return self._get_object_url("update", object, **kwargs)

    def get_delete_url(self, object, **kwargs):
        return self._get_object_url("delete", object, **kwargs)

    def get_list_url(self, **kwargs):
        return self.get_endpoint_url("list")

    def _create_breadcrumb(self, url, title):
        if url:
            return {
                "url": url,
                "title": title,
            }

        return None  # pragma: no cover

    def get_breadcrumbs(self):
        result = list()

        if self.parent:
            result.extend(self.parent.get_breadcrumbs())

        return result

    def _create_action(self, url, title):
        if url:
            return {
                "url": url,
                "title": title,
            }

        return None

    def get_read_action(self, object):
        return self._create_action(self.get_read_url(object=object), gettext("View"))

    def get_update_action(self, object):
        return self._create_action(self.get_update_url(object=object), gettext("Edit"))

    def get_delete_action(self, object):
        return self._create_action(
            self.get_delete_url(object=object), gettext("Delete")
        )

    def get_default_list_action(self, object):
        return self.get_read_action(object)

    def get_additional_list_actions(self, object):
        result = list()

        update_action = self.get_update_action(object=object)
        if update_action:
            result.append(update_action)

        delete_action = self.get_delete_action(object=object)
        if delete_action:
            result.append(delete_action)

        return result

    def get_all_list_actions(self, object):
        result = list()

        default_action = self.get_default_list_action(object)
        if default_action:
            result.append(default_action)

        result.extend(self.get_additional_list_actions(object))

        return result

    def get_additional_read_actions(self, object):
        result = list()

        update_action = self.get_update_action(object=object)
        if update_action:
            result.append(update_action)

        delete_action = self.get_delete_action(object=object)
        if delete_action:
            result.append(delete_action)

        return result

    def get_read_actions(self, object):
        result = list()

        result.extend(self.get_additional_read_actions(object))

        return result

    def _add_view(self, key, url, view_class, endpoint, app, **kwargs):
        if not issubclass(view_class, BaseView):  # pragma: no cover
            raise ValueError(f"view_class must inherit from {BaseView}")

        kwargs["handler"] = self
        app.add_url_rule(
            url,
            view_func=view_class.as_view(endpoint, **kwargs),
        )
        self.endpoints[key] = endpoint

    def get_model_name(self):
        return self.model.__model_name__

    def get_model_name_plural(self):
        return self.model.__model_name_plural__

    def get_permission_entity(self):
        return f"{self.generic_prefix}{self.get_model_name_plural()}"

    def get_single_url_folder(self):
        return f"{self.generic_prefix}{self.get_model_name()}"

    def get_plural_url_folder(self):
        return f"{self.generic_prefix}{self.get_model_name_plural()}"

    def get_single_endpoint_name(self):
        return f"{self.generic_prefix}{self.get_model_name()}"

    def get_plural_endpoint_name(self):
        return f"{self.generic_prefix}{self.get_model_name_plural()}"

    def get_id_query_arg_name(self):  # pragma: no cover
        return "id"

    def add_views(self, app):
        single_url_folder = self.get_single_url_folder()
        plural_url_folder = self.get_plural_url_folder()
        single_endpoint_name = self.get_single_endpoint_name()
        plural_endpoint_name = self.get_plural_endpoint_name()
        id_query_arg_name = self.get_id_query_arg_name()

        self._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        if self.create_view_class:

            class CreateView(self.create_view_class):
                decorators = self.create_decorators
                form_class = self.create_view_class.form_class or self.create_form_class

            self._add_view(
                "create",
                f"/{single_url_folder}/create",
                CreateView,
                f"{single_endpoint_name}_create",
                app,
            )

        if self.read_view_class:

            class ReadView(self.read_view_class):
                decorators = self.read_decorators
                display_class = self.read_display_class

            self._add_view(
                "read",
                f"/{single_url_folder}/<int:{id_query_arg_name}>",
                ReadView,
                single_endpoint_name,
                app,
            )

        if self.update_view_class:

            class UpdateView(self.update_view_class):
                decorators = self.update_decorators
                form_class = self.update_view_class.form_class or self.update_form_class
                display_class = self.update_display_class

            self._add_view(
                "update",
                f"/{single_url_folder}/<int:{id_query_arg_name}>/update",
                UpdateView,
                f"{single_endpoint_name}_update",
                app,
            )

        if self.delete_view_class:

            class DeleteView(self.delete_view_class):
                decorators = self.delete_decorators
                form_class = self.delete_view_class.form_class or self.delete_form_class

            self._add_view(
                "delete",
                f"/{single_url_folder}/<int:{id_query_arg_name}>/delete",
                DeleteView,
                f"{single_endpoint_name}_delete",
                app,
            )

        if self.list_view_class:
            list_form_class = self.list_view_class.form_class or self.list_form_class

            if list_form_class:
                list_form_class.filters = list_form_class.filters or self.list_filters
                list_form_class.search_definitions = (
                    list_form_class.search_definitions or self.list_search_definitions
                )
                list_form_class.sort_definitions = (
                    list_form_class.sort_definitions or self.list_sort_definitions
                )

            class ListView(self.list_view_class):
                decorators = self.list_decorators
                display_class = self.list_display_class
                form_class = list_form_class

            self._add_view(
                "list",
                f"/{plural_url_folder}",
                ListView,
                plural_endpoint_name,
                app,
            )

    def get_template_folder(self):
        return f"{self.generic_prefix}{self.get_model_name()}"

    def _init_template_pathes(self):
        if isinstance(self.app, Blueprint):
            self.template_pathes.append(f"{self.app.name}/")

        self.template_pathes.append("")

    def init_app(self, app):
        if isinstance(app, BaseBlueprint):
            app.view_handlers.append(self)

        self.app = app
        self._init_template_pathes()
        self.add_views(app)
