"""Reach log: one record per successful view of a single event page (`main.event`,
`main.event_date`) on the logger `eventcally.reach` (one JSON line with
`LOG_FORMAT=json`), naming the event (and date) and the source of the visit.

Never written: IP, user id, cookie, session, query string, path or user agent. The
referer is reduced to its host, source parameters are validated against a small
character set.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from flask import current_app, g, request

from project.infrastructure.logging_config import REACH_LOGGER

logger = logging.getLogger(__name__)

SOURCE_PARAM_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|embedly|preview|headless"
    r"|python-requests|curl|wget|httpclient|okhttp",
    re.IGNORECASE,
)
WIDGET_PATH_RE = re.compile(r"^/(custom_widget/|organizations/\d+/widget/)")
MAX_SOURCE_LENGTH = 255


def _param(name: str) -> Optional[str]:
    value = (request.args.get(name) or "").strip().lower()
    if not value:
        return None
    return value if SOURCE_PARAM_RE.match(value) else "invalid"


def _own_hostname() -> str:
    return (urlparse("//" + request.host).hostname or "").lower()


def _referer_source() -> str:
    referer = request.headers.get("Referer")
    if not referer:
        return "direct"

    try:
        parsed = urlparse(referer)
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        return "invalid"

    if not hostname:
        return "direct"

    if hostname == _own_hostname():
        return "widget" if WIDGET_PATH_RE.match(parsed.path or "") else "internal"

    return hostname[:MAX_SOURCE_LENGTH]


def request_source() -> tuple[str, Optional[str], Optional[str]]:
    source = _param("src") or _param("utm_source") or _referer_source()
    return source, _param("utm_medium"), _param("utm_campaign")


def is_bot(user_agent: Optional[str]) -> bool:
    return bool(user_agent and BOT_RE.search(user_agent))


def build_event_view_record(event_id: int, event_date_id: Optional[int]) -> dict:
    source, medium, campaign = request_source()
    return {
        "type": "reach",
        "request_id": g.get("request_id"),
        "endpoint": request.endpoint,
        "event_id": event_id,
        "event_date_id": event_date_id,
        "source": source,
        "medium": medium,
        "campaign": campaign,
        "bot": is_bot(request.user_agent.string),
    }


def log_event_view(event_id: int, event_date_id: Optional[int] = None):
    try:
        if not current_app.config.get("REACH_LOG"):
            return

        record = build_event_view_record(event_id, event_date_id)
        logging.getLogger(REACH_LOGGER).info("reach", extra=record)
    except Exception:
        logger.exception("Could not write the reach record")
