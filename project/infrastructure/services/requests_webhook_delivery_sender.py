import hashlib
import hmac
import json
import logging
from typing import Optional

import requests

from project.application.services.abstract_webhook_delivery_sender import (
    AbstractWebhookDeliverySender,
)


class RequestsWebhookDeliverySender(AbstractWebhookDeliverySender):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def send(
        self,
        *,
        url: str,
        secret: Optional[str],
        payload: dict,
        event_type: str,
        webhook_delivery_id: int,
        app_installation_id: Optional[int],
    ) -> tuple[str, Optional[str]]:
        headers = {
            "Content-Type": "application/json",
            "X-EventCally-Delivery-Id": str(webhook_delivery_id),
            "X-EventCally-Event": event_type,
        }

        if app_installation_id:
            headers["X-EventCally-App-Installation-Id"] = str(app_installation_id)

        data_str = json.dumps(payload)

        if secret:
            signature = hmac.new(
                secret.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            headers["X-EventCally-Signature-256"] = f"sha256={signature}"

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
        except requests.RequestException as exc:
            if exc.response:
                if isinstance(exc.response.reason, bytes):
                    try:
                        reason = exc.response.reason.decode("utf-8")
                    except UnicodeDecodeError:
                        reason = exc.response.reason.decode("iso-8859-1")
                else:
                    reason = exc.response.reason
                status = reason[:255] if reason else type(exc).__name__
            else:
                status = type(exc).__name__

        return status, status_code
