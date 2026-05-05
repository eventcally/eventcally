"""Celery app entrypoint for CLI commands.

This module keeps backward compatibility for commands like:
    celery -A project.celery worker
"""

from project import create_app
from project.celery_init import celery

# Initialize Flask app so init_celery() configures the shared Celery instance.
flask_app = create_app()

__all__ = ["celery", "flask_app"]
