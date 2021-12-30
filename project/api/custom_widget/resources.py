from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project import db
from project.access import access_or_401, login_api_user_or_401
from project.api import add_api_resource
from project.api.custom_widget.schemas import (
    CustomWidgetPatchRequestSchema,
    CustomWidgetPostRequestSchema,
    CustomWidgetSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import CustomWidget


class CustomWidgetResource(BaseResource):
    @doc(summary="Get custom widget", tags=["Custom Widgets"])
    @marshal_with(CustomWidgetSchema)
    def get(self, id):
        return CustomWidget.query.get_or_404(id)

    @doc(
        summary="Update custom widget",
        tags=["Custom Widgets"],
        security=[{"oauth2": ["customwidget:write"]}],
    )
    @use_kwargs(CustomWidgetPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("customwidget:write")
    def put(self, id):
        login_api_user_or_401()
        customwidget = CustomWidget.query.get_or_404(id)
        access_or_401(customwidget.adminunit, "admin_unit:update")

        customwidget = self.update_instance(
            CustomWidgetPostRequestSchema, instance=customwidget
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch custom widget",
        tags=["Custom Widgets"],
        security=[{"oauth2": ["customwidget:write"]}],
    )
    @use_kwargs(CustomWidgetPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_api_access("customwidget:write")
    def patch(self, id):
        login_api_user_or_401()
        customwidget = CustomWidget.query.get_or_404(id)
        access_or_401(customwidget.adminunit, "admin_unit:update")

        customwidget = self.update_instance(
            CustomWidgetPatchRequestSchema, instance=customwidget
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete custom widget",
        tags=["Custom Widgets"],
        security=[{"oauth2": ["customwidget:write"]}],
    )
    @marshal_with(None, 204)
    @require_api_access("customwidget:write")
    def delete(self, id):
        login_api_user_or_401()
        customwidget = CustomWidget.query.get_or_404(id)
        access_or_401(customwidget.adminunit, "admin_unit:update")

        db.session.delete(customwidget)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    CustomWidgetResource,
    "/custom-widgets/<int:id>",
    "api_v1_custom_widget",
)
