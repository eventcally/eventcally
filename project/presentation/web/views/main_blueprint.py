"""Main routes blueprint for general application routes."""

from flask import Blueprint

# Create main blueprint for general routes (home, legal pages, health checks, etc.)
main_bp = Blueprint("main", __name__)
