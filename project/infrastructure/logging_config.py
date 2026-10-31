"""Log output of the app, Celery and gunicorn.

Call sites keep using the stdlib `logging` (structured fields go through `extra=`).
Every handler renders through one structlog `ProcessorFormatter`: one JSON object per
line with `LOG_FORMAT=json` (the default), readable multi-line output with
`LOG_FORMAT=console` (local development, set in .flaskenv).
Context bound with `bind_log_context` (request id, Celery task) is added to each line.
"""

import logging
import os
import sys

import structlog
from gunicorn.glogging import Logger as BaseGunicornLogger

API_USAGE_LOGGER = "eventcally.api_usage"
GUNICORN_ACCESS_LOGGER = "gunicorn.access"
LOG_FORMATS = ("console", "json")


def get_log_format() -> str:
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    return log_format if log_format in LOG_FORMATS else "json"


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()


def bind_log_context(**values) -> dict:
    """Returns the tokens that `reset_log_context` restores the previous values with."""
    return dict(structlog.contextvars.bind_contextvars(**values))


def reset_log_context(tokens: dict):
    structlog.contextvars.reset_contextvars(**tokens)


def get_log_context() -> dict:
    return structlog.contextvars.get_contextvars()


def _drop_celery_data(_, __, event_dict: dict) -> dict:
    """Celery passes the task's args and kwargs as `extra={"data": ...}`; they may hold
    personal data and never went into the plain lines either."""
    if event_dict["_record"].name.startswith("celery"):
        event_dict.pop("data", None)
    return event_dict


def _drop_positional_args(_, __, event_dict: dict) -> dict:
    event_dict.pop("positional_args", None)
    return event_dict


def _gunicorn_access_fields(_, __, event_dict: dict) -> dict:
    """JSON access lines as fields instead of GUNICORN_ACCESS_LOG_FORMAT. The query
    string stays out, it may carry tokens."""
    args = event_dict.pop("positional_args", None)

    if event_dict["_record"].name != GUNICORN_ACCESS_LOGGER or not isinstance(
        args, dict
    ):
        return event_dict

    status = args.get("s")
    event_dict.update(
        event=f"{args.get('m')} {args.get('U')} {status}",
        method=args.get("m"),
        path=args.get("U"),
        status=int(status) if str(status).isdigit() else status,
        duration_ms=args.get("M"),
        bytes=args.get("B"),
        remote_addr=args.get("h"),
        user_agent=args.get("a"),
        request_id=args.get("{x-request-id}o"),
    )
    return event_dict


def build_formatter(log_format: str | None = None) -> logging.Formatter:
    if (log_format or get_log_format()) == "json":
        args_processor = _gunicorn_access_fields
        final_processors = [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        args_processor = _drop_positional_args
        final_processors = [
            structlog.dev.ConsoleRenderer(
                colors=False,
                pad_level=False,
                exception_formatter=structlog.dev.plain_traceback,
            )
        ]

    return structlog.stdlib.ProcessorFormatter(
        # the access processor needs gunicorn's atoms, which are the record's args
        pass_foreign_args=True,
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.ExtraAdder(),
            _drop_celery_data,
            args_processor,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *final_processors,
        ],
    )


def use_log_formatter(logger: logging.Logger, formatter: logging.Formatter = None):
    """Renders the handlers a library set up (gunicorn, Celery) through ours."""
    formatter = formatter or build_formatter()

    for handler in logger.handlers:
        handler.setFormatter(formatter)


def init_logging(log_format: str | None = None, stream=None):
    """The root logger writes everything; safe to call more than once."""
    root = logging.getLogger()
    handler = next((h for h in root.handlers if getattr(h, "_eventcally", False)), None)

    if handler is None:
        handler = logging.StreamHandler(stream or sys.stderr)
        handler._eventcally = True
        root.addHandler(handler)

    handler.setFormatter(build_formatter(log_format))
    root.setLevel(get_log_level())
    # every API request is recorded, whatever LOG_LEVEL says
    logging.getLogger(API_USAGE_LOGGER).setLevel(logging.INFO)


class GunicornLogger(BaseGunicornLogger):
    """`logger_class` in gunicorn.conf.py: gunicorn's own lines (boot, worker timeouts,
    access) in the same format as the app's."""

    def setup(self, cfg):
        super().setup(cfg)
        formatter = build_formatter()
        use_log_formatter(self.error_log, formatter)
        use_log_formatter(self.access_log, formatter)
