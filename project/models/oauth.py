import datetime
import time

from authlib.integrations.sqla_oauth2 import (
    OAuth2AuthorizationCodeMixin,
    OAuth2ClientMixin,
    OAuth2TokenMixin,
)
from flask import request
from sqlalchemy.orm import object_session

from project import db
from project.dateutils import gmt_tz

# OAuth Server: Wir bieten an, dass sich ein Nutzer per OAuth2 auf unserer Seite anmeldet
oauth_refresh_token_expires_in = 90 * 86400  # 90 days


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = "oauth2_client"
    __display_name__ = "OAuth2 client"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    @OAuth2ClientMixin.grant_types.getter
    def grant_types(self):
        return ["authorization_code", "refresh_token", "client_credentials"]

    @OAuth2ClientMixin.response_types.getter
    def response_types(self):
        return ["code"]

    @OAuth2ClientMixin.token_endpoint_auth_method.getter
    def token_endpoint_auth_method(self):
        return ["client_secret_basic", "client_secret_post", "none"]

    def check_redirect_uri(self, redirect_uri):
        if redirect_uri.startswith(request.host_url):  # pragma: no cover
            return True

        return super().check_redirect_uri(redirect_uri)

    def check_token_endpoint_auth_method(self, method):
        return method in self.token_endpoint_auth_method

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == "token":
            return self.check_token_endpoint_auth_method(method)

        return True

    def __str__(self):
        return self.client_name or super().__str__()


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_code"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = "oauth2_token"
    __display_name__ = "OAuth2 token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    @property
    def client(self):
        return (
            object_session(self)
            .query(OAuth2Client)
            .filter(OAuth2Client.client_id == self.client_id)
            .first()
        )

    @property
    def expires_at(self):
        return self.issued_at + self.expires_in

    def is_refresh_token_active(self):
        if self.is_revoked():
            return False

        refresh_token_expires_at = self.issued_at + oauth_refresh_token_expires_in
        return refresh_token_expires_at >= time.time()

    def revoke_token(self):
        self.access_token_revoked_at = int(time.time())

    @property
    def expires_at_datetime(self):
        return datetime.datetime.fromtimestamp(self.expires_at, gmt_tz)

    @property
    def issued_at_datetime(self):
        return datetime.datetime.fromtimestamp(self.issued_at, gmt_tz)

    @property
    def client_name(self):
        return self.client.client_name

    def __str__(self):
        return f"{super().__str__()} ({self.client_name})"
