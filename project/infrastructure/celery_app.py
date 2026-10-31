from contextlib import contextmanager
from smtplib import SMTPException
from urllib.error import URLError

from babel import Locale
from celery import Celery
from celery import Task as BaseTask
from celery.signals import (
    after_setup_logger,
    after_setup_task_logger,
    before_task_publish,
    task_postrun,
    task_prerun,
)
from flask import current_app
from requests.exceptions import RequestException


class HttpTaskException(Exception):
    pass


# Create unbound celery instance (configured by init_celery)
celery = Celery()


def init_celery(app):
    """Initialize Celery with Flask app configuration."""
    celery.main = app.import_name
    celery.conf.update(app.config["CELERY_CONFIG"])
    TaskBase = BaseTask

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    class HttpTask(ContextTask):
        abstract = True
        autoretry_for = (HttpTaskException,)
        retry_backoff = 5
        max_retries = 3
        retry_jitter = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._real_run = self.run
            self.run = self._wrapped_run

        def _wrapped_run(self, *args, **kwargs):
            try:
                self._real_run(*args, **kwargs)
            except (
                URLError,
                RequestException,
                SMTPException,
            ) as e:
                raise HttpTaskException(repr(e))

    setattr(app, "celery_http_task_cls", HttpTask)


@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_logger(logger, *args, **kwargs):
    from project.infrastructure.logging_config import use_log_formatter

    use_log_formatter(logger)


@before_task_publish.connect
def pass_request_id(headers=None, **kwargs):
    """Tasks queued during a request log with its request id."""
    from project.infrastructure.logging_config import get_log_context

    request_id = get_log_context().get("request_id")

    if headers is not None and request_id:
        headers.setdefault("request_id", request_id)


@task_prerun.connect
def bind_task_log_context(task_id=None, task=None, **kwargs):
    from project.infrastructure.logging_config import bind_log_context, get_log_context

    request_id = task.request.get("request_id") or get_log_context().get("request_id")
    context = {"task_id": task_id, "task_name": task.name}

    if request_id:
        context["request_id"] = request_id

    # Eager tasks run inside the request: postrun restores its context, not clears it
    task.request.log_context_tokens = bind_log_context(**context)


@task_postrun.connect
def reset_task_log_context(task=None, **kwargs):
    from project.infrastructure.logging_config import reset_log_context

    tokens = getattr(task.request, "log_context_tokens", None)

    if tokens:
        task.request.log_context_tokens = None
        reset_log_context(tokens)


@contextmanager
def force_locale(locale=None, app=None):
    """
    Force a specific locale in a context.

    Args:
        locale: The locale to use (defaults to 'de')
        app: The Flask app instance (defaults to current_app)
    """
    if app is None:
        app = current_app._get_current_object()

    if not locale:
        locale = Locale.parse("de")

    with app.test_request_context() as ctx:
        ctx.babel_locale = locale
        yield
