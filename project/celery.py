"""Celery app entrypoint for CLI commands.

This module keeps backward compatibility for commands like:
    celery -A project.celery worker
"""

from project.celery_init import celery
from project.factory import create_app

# Initialize Flask app so init_celery() configures the shared Celery instance.
# Worker, beat and flower hold DB connections for long; keep them fresh.
flask_app = create_app(
    {"SQLALCHEMY_ENGINE_OPTIONS": {"pool_recycle": 60, "pool_pre_ping": True}}
)

__all__ = ["celery", "flask_app"]
