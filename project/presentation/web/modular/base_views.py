from typing import Optional

from flask.views import View
from flask_babel import lazy_gettext

from project.application.query_bus import QueryBus
from project.presentation.shared.permissions import PermissionAction


class BaseView(View):
    permission: str = None
    permission_action: PermissionAction = None

    def __init__(self, *args, **kwargs):
        from project.presentation.web.modular.base_view_handler import BaseViewHandler

        super().__init__()

        self.handler: Optional[BaseViewHandler] = kwargs.get("handler")

    @property
    def query_bus(self) -> QueryBus:
        return self.handler.query_bus

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        view = super().as_view(name, *class_args, **class_kwargs)

        for decorator in class_kwargs.get("handler").decorators:
            view = decorator(view)

        for decorator in class_kwargs.get("decorators", []):
            view = decorator(view)

        return view

    def get_title(self, **kwargs):  # pragma: no cover
        return ""

    def check_access(self, **kwargs):
        return self.handler.check_access(**kwargs)


class BaseListView(BaseView):
    permission_action = PermissionAction.read

    def get_title(self, **kwargs):
        return self.handler.get_model_display_name_plural()


class BaseObjectView(BaseView):
    def get_object_from_kwargs(self, **kwargs):
        return self.handler.get_object_from_kwargs(**kwargs)

    def check_object_access(self, object):
        return self.handler.check_object_access(object)


class BaseReadView(BaseObjectView):
    permission_action = PermissionAction.read

    def get_title(self, **kwargs):
        return self.handler.get_object_title(kwargs["object"])


class BaseCreateView(BaseView):
    permission_action = PermissionAction.write

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Create %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )


class BaseObjectFormView(BaseObjectView):
    pass


class BaseUpdateView(BaseObjectFormView):
    permission_action = PermissionAction.write

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Update %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )


class BaseDeleteView(BaseObjectFormView):
    permission_action = PermissionAction.write

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Delete %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )
