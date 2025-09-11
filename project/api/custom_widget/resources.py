from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project import db
from project.api import add_api_resource
from project.api.custom_widget.schemas import (
    CustomWidgetPatchRequestSchema,
    CustomWidgetPostRequestSchema,
    CustomWidgetSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.models import CustomWidget


class CustomWidgetResource(BaseResource):
    @doc(summary="Get custom widget", tags=["Custom Widgets"])
    @marshal_with(CustomWidgetSchema)
    @require_api_access("organization.custom_widgets:read")
    def get(self, id):
        customwidget = CustomWidget.query.get_or_404(id)
        return customwidget

    @doc(
        summary="Update custom widget",
        tags=["Custom Widgets"],
    )
    @use_kwargs(CustomWidgetPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.custom_widgets:write", CustomWidget)
    def put(self, id):
        customwidget = g.manage_admin_unit_instance
        customwidget = self.update_instance(
            CustomWidgetPostRequestSchema, instance=customwidget
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch custom widget",
        tags=["Custom Widgets"],
    )
    @use_kwargs(CustomWidgetPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.custom_widgets:write", CustomWidget)
    def patch(self, id):
        customwidget = g.manage_admin_unit_instance
        customwidget = self.update_instance(
            CustomWidgetPatchRequestSchema, instance=customwidget
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete custom widget",
        tags=["Custom Widgets"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.custom_widgets:write", CustomWidget)
    def delete(self, id):
        customwidget = g.manage_admin_unit_instance
        db.session.delete(customwidget)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    CustomWidgetResource,
    "/custom-widgets/<int:id>",
    "api_v1_custom_widget",
)
