"""Export webhook payload schemas as machine-readable JSON Schema."""

from pydantic.json_schema import models_json_schema

from project.application.webhooks.app_installation_webhooks import (
    app_installation_webhook_infos,
)
from project.application.webhooks.app_webhooks import app_webhook_infos


def export_all_webhook_schemas() -> dict:
    all_webhook_infos = app_webhook_infos + app_installation_webhook_infos
    payload_classes = [info.payload_cls for info in all_webhook_infos]

    # Generate combined schemas once (shared refs/defs)
    _, top_level_schema = models_json_schema(
        [(payload_cls, "serialization") for payload_cls in payload_classes],
        title="Webhook Payload Schemas",
    )
    return top_level_schema
