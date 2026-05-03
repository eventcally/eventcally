import datetime
import hashlib
import hmac
import json
import logging

import requests

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt


class WebhookDeliveryService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def send_webhook_delivery_sync(
        self, uow: AbstractUnitOfWork, webhook_delivery_id: int
    ):
        webhook_delivery = uow.webhooks.get_delivery(webhook_delivery_id)
        if not webhook_delivery:
            return

        webhook = webhook_delivery.webhook
        webhook_event = webhook_delivery.webhook_event

        webhook_delivery_id = webhook_delivery.id
        url = webhook.url
        secret = webhook.secret
        json_dict = webhook_event.payload
        event_type = webhook_event.event_type
        app_installation_id = webhook_delivery.app_installation_id

        headers = {
            "Content-Type": "application/json",
            "X-EventCally-Delivery-Id": str(webhook_delivery_id),
            "X-EventCally-Event": event_type,
        }

        if app_installation_id:
            headers["X-EventCally-App-Installation-Id"] = str(app_installation_id)

        data_str = json.dumps(json_dict)

        if secret:
            signature = hmac.new(
                secret.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            headers["X-EventCally-Signature-256"] = f"sha256={signature}"

        start_at = datetime.datetime.now(datetime.timezone.utc)
        status_code = None

        try:
            response = requests.post(
                url, data=data_str.encode("utf-8"), headers=headers, timeout=10
            )
            status_code = str(response.status_code) if response.status_code else None
            response.raise_for_status()
            status = "OK"
        except requests.Timeout:
            status = "Timeout"
        except requests.RequestException as e:
            if e.response:
                if isinstance(e.response.reason, bytes):
                    try:
                        reason = e.response.reason.decode("utf-8")
                    except UnicodeDecodeError:
                        reason = e.response.reason.decode("iso-8859-1")
                else:
                    reason = e.response.reason
                status = reason[:255] if reason else type(e).__name__
            else:
                status = type(e).__name__
        finally:
            end_at = datetime.datetime.now(datetime.timezone.utc)

        attempt = WebhookDeliveryAttempt(
            url=url,
            status=status,
            status_code=status_code,
            start_at=start_at,
            end_at=end_at,
        )
        webhook_delivery.attempts.append(attempt)
