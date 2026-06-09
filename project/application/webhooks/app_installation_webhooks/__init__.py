from typing import Optional

from project.application.webhooks import payloads
from project.application.webhooks.app_installation_webhooks.app_installation_webhook_info import (
    AppInstallationWebhookInfo,
)

app_installation_webhook_infos: list[AppInstallationWebhookInfo] = list()
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event",
        action="created",
        permissions=["events:read"],
        payload_cls=payloads.EventCreatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event",
        action="updated",
        permissions=["events:read"],
        payload_cls=payloads.EventUpdatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event",
        action="deleted",
        permissions=["events:read"],
        payload_cls=payloads.EventDeletedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_organizer",
        action="created",
        permissions=["event_organizers:read"],
        payload_cls=payloads.EventOrganizerCreatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_organizer",
        action="updated",
        permissions=["event_organizers:read"],
        payload_cls=payloads.EventOrganizerUpdatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_organizer",
        action="deleted",
        permissions=["event_organizers:read"],
        payload_cls=payloads.EventOrganizerDeletedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_place",
        action="created",
        permissions=["event_places:read"],
        payload_cls=payloads.EventPlaceCreatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_place",
        action="updated",
        permissions=["event_places:read"],
        payload_cls=payloads.EventPlaceUpdatedPayload,
    )
)
app_installation_webhook_infos.append(
    AppInstallationWebhookInfo(
        entity="event_place",
        action="deleted",
        permissions=["event_places:read"],
        payload_cls=payloads.EventPlaceDeletedPayload,
    )
)


def get_app_installation_webhook_info_by_event_type(
    event_type: str,
) -> Optional[AppInstallationWebhookInfo]:
    for info in app_installation_webhook_infos:
        if info.event_type == event_type:
            return info
    return None
