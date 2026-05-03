"""OAuth2 authorization objects.

These are created here and initialized via config_oauth() function.
"""

from authlib.integrations.flask_oauth2 import ResourceProtector

# OAuth2 extension instances (not bound to app yet)
authorization = None  # Will be created in config_oauth()
require_oauth = ResourceProtector()
