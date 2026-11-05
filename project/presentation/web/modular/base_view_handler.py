from typing import Annotated, Optional

from dependency_injector.providers import Factory
from dependency_injector.wiring import Provider
from flask import Blueprint, abort, current_app, url_for
from flask_babel import gettext

from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.web.modular.base_blueprint import BaseBlueprint
from project.presentation.web.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseReadView,
    BaseUpdateView,
    BaseView,
)


class BaseViewHandler:
    decorators = []
    query_bus_factory: Annotated[
        Factory[QueryBus], Provider[Application.cqrs.query_bus]
    ]
    # These name the entity (URLs, endpoints, permissions, titles). Display names are
    # English msgids, translated at call time.
    model_name = None
    model_name_plural = None
    display_name = None
    display_name_plural = None
    create_view_class = BaseCreateView
    create_decorators = []
    read_view_class = BaseReadView
    read_decorators = []
    update_view_class = BaseUpdateView
    update_decorators = []
    delete_view_class = BaseDeleteView
    delete_decorators = []
    list_view_class = BaseListView
    list_decorators = []
    generic_prefix = ""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.parent: Optional[BaseViewHandler] = kwargs.get("parent", None)
        self.app = None
        self.endpoints = dict()
        self.permissions = set()

    @property
    def query_bus(self) -> QueryBus:
        return self.query_bus_factory()

    def get_model_display_name(self):
        return gettext(self.display_name)

    def get_model_display_name_plural(self):
        return gettext(self.display_name_plural)

    def get_object_title(self, object) -> str:  # pragma: no cover
        return str(object)

    def get_object_from_kwargs(self, **kwargs):
        object_id = kwargs.get(self.get_id_query_arg_name())
        object = self.get_object_by_id(object_id)

        if not object:  # pragma: no cover
            abort(404)

        return object

    def get_object_by_id(self, object_id):
        return self.query_bus.handle(self.create_get_query(object_id))

    def create_get_query(self, object_id):
        """The Query whose result is the object (a read model) or `None`."""
        raise NotImplementedError  # pragma: no cover

    def check_object_access(self, object):  # pragma: no cover
        return None

    def check_access(self, **kwargs):
        return None

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

    def get_list_url(self, **kwargs):
        return self.get_endpoint_url("list")

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
        return self.model_name

    def get_model_name_plural(self):
        return self.model_name_plural

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

            self._add_view(
                "delete",
                f"/{single_url_folder}/<int:{id_query_arg_name}>/delete",
                DeleteView,
                f"{single_endpoint_name}_delete",
                app,
            )

        if self.list_view_class:

            class ListView(self.list_view_class):
                decorators = self.list_decorators

            self._add_view(
                "list",
                f"/{plural_url_folder}",
                ListView,
                plural_endpoint_name,
                app,
            )

    def init_app(self, app):
        if isinstance(app, BaseBlueprint):
            app.view_handlers.append(self)

        self.app = app
        self.add_views(app)
