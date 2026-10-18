"""OAuth2 authorization objects.

These are created here and assigned by the app factory.
"""

from authlib.integrations.flask_oauth2 import ResourceProtector

# OAuth2 extension instances (not bound to app yet)
authorization = None  # Assigned by the app factory
require_oauth = ResourceProtector()
