import io
import json
import logging
import sys

import pytest
from gunicorn.config import Config
from gunicorn.glogging import SafeAtoms

from project.infrastructure.logging_config import (
    API_USAGE_LOGGER,
    GUNICORN_ACCESS_LOGGER,
    GunicornLogger,
    bind_log_context,
    build_formatter,
    get_log_context,
    get_log_format,
    get_log_level,
    init_logging,
    reset_log_context,
    use_log_formatter,
)


def _record(name="project.test", level=logging.INFO, msg="hello %s", args=("you",)):
    return logging.LogRecord(name, level, __file__, 1, msg, args, None)


def _json(record, log_format="json"):
    return json.loads(build_formatter(log_format).format(record))


@pytest.fixture
def root_logger():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    root.handlers = [h for h in handlers if not getattr(h, "_eventcally", False)]
    yield root
    root.handlers, root.level = handlers, level


@pytest.mark.parametrize(
    "value, expected", [(None, "json"), ("Console", "console"), ("xml", "json")]
)
def test_log_format_from_env(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("LOG_FORMAT", raising=False)
    else:
        monkeypatch.setenv("LOG_FORMAT", value)

    assert get_log_format() == expected


def test_log_level_from_env(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert get_log_level() == "INFO"

    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert get_log_level() == "DEBUG"


def test_json_line_has_fields_and_context():
    record = _record()
    record.user_id = 5
    tokens = bind_log_context(request_id="r1")

    try:
        line = _json(record)
    finally:
        reset_log_context(tokens)

    assert line["event"] == "hello you"
    assert line["level"] == "info"
    assert line["logger"] == "project.test"
    assert line["request_id"] == "r1"
    assert line["user_id"] == 5
    assert line["timestamp"].endswith("Z")
    assert "positional_args" not in line
    assert "request_id" not in get_log_context()


def test_json_line_has_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            "project.test", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
        )

    line = _json(record)

    assert line["level"] == "error"
    assert "ValueError: boom" in line["exception"]


def test_console_line_keeps_bracketed_level():
    line = build_formatter("console").format(_record(level=logging.ERROR))

    assert "[error] hello you" in line
    assert "\n" not in line


def test_json_access_line_has_fields_without_query():
    atoms = SafeAtoms(
        {
            "h": "1.2.3.4",
            "m": "GET",
            "U": "/api/v1/events",
            "q": "access_token=secret",
            "r": "GET /api/v1/events?access_token=secret HTTP/1.1",
            "s": "200",
            "M": 3,
            "B": 10,
            "a": "agent",
            "{x-request-id}o": "r2",
        }
    )
    record = _record(GUNICORN_ACCESS_LOGGER, msg='%(h)s "%(r)s"', args=(atoms,))

    line = _json(record)

    assert line["event"] == "GET /api/v1/events 200"
    assert line["status"] == 200
    assert line["path"] == "/api/v1/events"
    assert line["method"] == "GET"
    assert line["duration_ms"] == 3
    assert line["bytes"] == 10
    assert line["remote_addr"] == "1.2.3.4"
    assert line["user_agent"] == "agent"
    assert line["request_id"] == "r2"
    assert "secret" not in json.dumps(line)


def test_json_access_line_without_atoms_stays_as_is():
    line = _json(_record(GUNICORN_ACCESS_LOGGER, msg="plain", args=()))

    assert line["event"] == "plain"
    assert "status" not in line


def test_console_access_line_keeps_the_access_format():
    atoms = SafeAtoms({"h": "1.2.3.4", "r": "GET / HTTP/1.1"})
    record = _record(GUNICORN_ACCESS_LOGGER, msg='%(h)s "%(r)s"', args=(atoms,))

    line = build_formatter("console").format(record)

    assert '[info] 1.2.3.4 "GET / HTTP/1.1"' in line
    assert "positional_args" not in line


def test_use_log_formatter():
    logger = logging.getLogger("test.use_log_formatter")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.propagate = False

    try:
        use_log_formatter(logger, build_formatter("json"))
        logger.warning("library line")
    finally:
        logger.removeHandler(handler)

    assert json.loads(stream.getvalue())["event"] == "library line"


def test_init_logging_is_safe_to_repeat(root_logger, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    stream = io.StringIO()

    init_logging("console", stream=stream)
    init_logging("json", stream=io.StringIO())
    logging.getLogger("project.test").warning("once")

    ours = [h for h in root_logger.handlers if getattr(h, "_eventcally", False)]
    assert len(ours) == 1
    assert json.loads(stream.getvalue())["event"] == "once"
    assert root_logger.level == logging.WARNING
    # the API usage records still pass
    assert logging.getLogger(API_USAGE_LOGGER).getEffectiveLevel() == logging.INFO


def test_gunicorn_logger_uses_our_format(monkeypatch):
    monkeypatch.setenv("LOG_FORMAT", "json")
    cfg = Config()
    cfg.set("accesslog", "-")
    error_log = logging.getLogger("gunicorn.error")
    access_log = logging.getLogger(GUNICORN_ACCESS_LOGGER)

    try:
        logger = GunicornLogger(cfg)
        formatters = [h.formatter for h in error_log.handlers + access_log.handlers]
    finally:
        error_log.handlers, access_log.handlers = [], []

    assert logger.error_log is error_log
    assert formatters
    assert all(
        json.loads(formatter.format(_record()))["event"] == "hello you"
        for formatter in formatters
    )


def test_celery_task_data_is_dropped():
    record = _record("celery.app.trace", msg="Task succeeded", args=())
    record.data = {"args": "('personal',)"}
    app_record = _record(msg="app", args=())
    app_record.data = {"kept": True}

    assert "data" not in _json(record)
    assert _json(app_record)["data"] == {"kept": True}
