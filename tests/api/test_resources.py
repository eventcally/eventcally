import pytest


def test_create_instance_calls_validate_when_present(app):
    """`BaseResource.create_instance` calls `.validate()` on the loaded model
    instance when it defines one — exercised here directly against a real
    aggregate (`Webhook`) since no currently-migrated API resource still
    routes a validate()-having model through this generic reflection hook."""
    from project.api.resources import BaseResource
    from project.api.schemas import SQLAlchemyBaseSchema
    from project.models.webhook import Webhook

    class WebhookModelSchema(SQLAlchemyBaseSchema):
        class Meta:
            model = Webhook
            load_instance = True

    with app.test_request_context(json={}):
        resource = BaseResource()

        with pytest.raises(ValueError, match="URL is required for a webhook"):
            resource.create_instance(WebhookModelSchema)
