from typing import Optional

from project.application.webhooks import payloads
from project.application.webhooks.app_webhooks.app_webhook_info import AppWebhookInfo

app_webhook_infos: list[AppWebhookInfo] = list()
app_webhook_infos.append(
    AppWebhookInfo(
        entity="app",
        action="installed",
        payload_cls=payloads.AppInstallationCreatedPayload,
    )
)
app_webhook_infos.append(
    AppWebhookInfo(
        entity="app",
        action="uninstalled",
        payload_cls=payloads.AppInstallationDeletedPayload,
    )
)
app_webhook_infos.append(
    AppWebhookInfo(
        entity="app_installation",
        action="permissions_updated",
        payload_cls=payloads.AppInstallationPermissionsUpdatedPayload,
    )
)


def get_app_webhook_info_by_event_type(
    event_type: str,
) -> Optional[AppWebhookInfo]:
    for info in app_webhook_infos:
        if info.event_type == event_type:
            return info
    return None
