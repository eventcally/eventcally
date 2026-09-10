from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.custom_widget.schemas import (
    CustomWidgetPatchRequestPlainSchema,
    CustomWidgetPatchRequestSchema,
    CustomWidgetPostRequestSchema,
    CustomWidgetPutRequestPlainSchema,
    CustomWidgetSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.application.commands import DeleteCustomWidgetCommand
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
        cmd = CustomWidgetPutRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Patch custom widget",
        tags=["Custom Widgets"],
    )
    @use_kwargs(CustomWidgetPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.custom_widgets:write", CustomWidget)
    def patch(self, id):
        cmd = CustomWidgetPatchRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Delete custom widget",
        tags=["Custom Widgets"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.custom_widgets:write", CustomWidget)
    def delete(self, id):
        cmd = DeleteCustomWidgetCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    CustomWidgetResource,
    "/custom-widgets/<int:id>",
    "api_v1_custom_widget",
)
