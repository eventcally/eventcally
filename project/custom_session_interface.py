from flask import request
from flask.sessions import SecureCookieSessionInterface


class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        if "authorization" in request.headers:
            return
        return super(CustomSessionInterface, self).save_session(*args, **kwargs)
