from flask import url_for

from project.views.base_views import (
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
    read_view_class = BaseReadView
    read_form_class = None
    update_view_class = BaseUpdateView
    update_form_class = None
    delete_view_class = BaseDeleteView
    delete_form_class = None
    list_view_class = BaseListView

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.endpoints = dict()

    def complete_object(self, object):  # pragma: no cover
        pass

    def check_object_access(self, object):  # pragma: no cover
        pass

    def get_objects_query_from_kwargs(self, **kwargs):
        return self.apply_objects_query_order(self.apply_base_filter(self.model.query))

    def apply_base_filter(self, query, **kwargs):  # pragma: no cover
        return query

    def apply_objects_query_order(self, query, **kwargs):  # pragma: no cover
        return query

    def can_object_be_deleted(self, form, object):  # pragma: no cover
        return True

    def get_endpoint_url(self, endpoint_key, **kwargs):
        endpoint = self.endpoints.get(endpoint_key)
        if endpoint:
            return url_for(endpoint, **kwargs)
        return None  # pragma: no cover

    def get_read_url(self, object, **kwargs):
        return self.get_endpoint_url("read", id=object.id)

    def get_create_url(self, object, **kwargs):
        return self.get_endpoint_url("create")

    def get_update_url(self, object, **kwargs):
        return self.get_endpoint_url("update", id=object.id)

    def get_delete_url(self, object, **kwargs):
        return self.get_endpoint_url("delete", id=object.id)

    def get_list_url(self, **kwargs):
        return self.get_endpoint_url("list")

    def _add_view(self, key, url, view_class, endpoint, app):
        app.add_url_rule(
            url,
            view_func=view_class.as_view(endpoint, handler=self),
        )
        self.endpoints[key] = endpoint

    def get_breadcrumbs(self):
        return list()

    def init_app(self, app):
        url_prefix = self.model.__model_name__
        endpoint_prefix = self.model.__model_name__

        if self.create_view_class:

            class CreateView(self.create_view_class):
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
                form_class = self.read_form_class

            self._add_view(
                "read",
                f"/{url_prefix}/<int:id>",
                ReadView,
                endpoint_prefix,
                app,
            )

        if self.update_view_class:

            class UpdateView(self.update_view_class):
                form_class = self.update_form_class

            self._add_view(
                "update",
                f"/{url_prefix}/<int:id>/update",
                UpdateView,
                f"{endpoint_prefix}_update",
                app,
            )

        if self.delete_view_class:

            class DeleteView(self.delete_view_class):
                form_class = self.delete_form_class

            self._add_view(
                "delete",
                f"/{url_prefix}/<int:id>/delete",
                DeleteView,
                f"{endpoint_prefix}_delete",
                app,
            )

        if self.list_view_class:

            class ListView(self.list_view_class):
                pass

            self._add_view(
                "list",
                f"/{self.model.__model_name_plural__}",
                ListView,
                self.model.__model_name_plural__,
                app,
            )
