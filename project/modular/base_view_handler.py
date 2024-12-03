from flask import Blueprint, url_for
from flask_babel import gettext

from project.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseReadView,
    BaseUpdateView,
)


class BaseViewHandler:
    decorators = []
    model = None
    create_view_class = BaseCreateView
    create_form_class = None
    create_decorators = []
    read_view_class = BaseReadView
    read_display_class = None
    read_decorators = []
    update_view_class = BaseUpdateView
    update_form_class = None
    update_decorators = []
    delete_view_class = BaseDeleteView
    delete_form_class = None
    delete_decorators = []
    list_view_class = BaseListView
    list_display_class = BaseListView
    list_decorators = []

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.app = None
        self.endpoints = dict()
        self.template_pathes = list()

    def complete_object(self, object):  # pragma: no cover
        pass

    def check_object_access(self, object):  # pragma: no cover
        return None

    def check_access(self, **kwargs):
        return None

    def get_objects_query_from_kwargs(self, **kwargs):
        return self.apply_objects_query_order(self.apply_base_filter(self.model.query))

    def apply_base_filter(self, query, **kwargs):  # pragma: no cover
        return query

    def apply_objects_query_order(self, query, **kwargs):  # pragma: no cover
        return query

    def can_object_be_deleted(self, form, object):  # pragma: no cover
        return True

    def get_list_per_page(self):
        return 20

    def get_endpoint_url(self, endpoint_key, **kwargs):
        endpoint = self.endpoints.get(endpoint_key)
        if endpoint:
            app_endpoint = (
                f".{endpoint}" if isinstance(self.app, Blueprint) else endpoint
            )
            return url_for(app_endpoint, **kwargs)
        return None  # pragma: no cover

    def get_read_url(self, object, **kwargs):
        kwargs.setdefault(self.get_id_query_arg_name(), object.id)
        return self.get_endpoint_url("read", **kwargs)

    def get_create_url(self, object, **kwargs):
        return self.get_endpoint_url("create")

    def get_update_url(self, object, **kwargs):
        kwargs.setdefault(self.get_id_query_arg_name(), object.id)
        return self.get_endpoint_url("update", **kwargs)

    def get_delete_url(self, object, **kwargs):
        kwargs.setdefault(self.get_id_query_arg_name(), object.id)
        return self.get_endpoint_url("delete", **kwargs)

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
        return list()

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

    def get_read_actions(self, object):
        result = list()

        update_action = self.get_update_action(object=object)
        if update_action:
            result.append(update_action)

        delete_action = self.get_delete_action(object=object)
        if delete_action:
            result.append(delete_action)

        return result

    def _add_view(self, key, url, view_class, endpoint, app):
        app.add_url_rule(
            url,
            view_func=view_class.as_view(endpoint, handler=self),
        )
        self.endpoints[key] = endpoint

    def get_url_prefix(self):
        return self.model.__model_name__

    def get_endpoint_prefix(self):
        return self.model.__model_name__

    def get_id_query_arg_name(self):  # pragma: no cover
        return "id"

    def add_views(self, app):
        url_prefix = self.get_url_prefix()
        endpoint_prefix = self.get_endpoint_prefix()
        id_query_arg_name = self.get_id_query_arg_name()

        if self.create_view_class:

            class CreateView(self.create_view_class):
                decorators = self.create_decorators
                form_class = self.create_form_class

            self._add_view(
                "create",
                f"/{url_prefix}/create",
                CreateView,
                f"{endpoint_prefix}_create",
                app,
            )

        if self.read_view_class:

            class ReadView(self.read_view_class):
                self.decorators = self.read_decorators
                display_class = self.read_display_class

            self._add_view(
                "read",
                f"/{url_prefix}/<int:{id_query_arg_name}>",
                ReadView,
                endpoint_prefix,
                app,
            )

        if self.update_view_class:

            class UpdateView(self.update_view_class):
                decorators = self.update_decorators
                form_class = self.update_form_class

            self._add_view(
                "update",
                f"/{url_prefix}/<int:{id_query_arg_name}>/update",
                UpdateView,
                f"{endpoint_prefix}_update",
                app,
            )

        if self.delete_view_class:

            class DeleteView(self.delete_view_class):
                decorators = self.delete_decorators
                form_class = self.delete_form_class

            self._add_view(
                "delete",
                f"/{url_prefix}/<int:{id_query_arg_name}>/delete",
                DeleteView,
                f"{endpoint_prefix}_delete",
                app,
            )

        if self.list_view_class:

            class ListView(self.list_view_class):
                decorators = self.list_decorators
                display_class = self.list_display_class

            self._add_view(
                "list",
                f"/{self.model.__model_name_plural__}",
                ListView,
                self.model.__model_name_plural__,
                app,
            )

    def _init_template_pathes(self):
        if isinstance(self.app, Blueprint):
            self.template_pathes.append(f"{self.app.name}/")

        self.template_pathes.append("")

    def init_app(self, app):
        self.app = app
        self._init_template_pathes()
        self.add_views(app)