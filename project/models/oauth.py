import datetime
import time

from authlib.integrations.sqla_oauth2 import (
    OAuth2AuthorizationCodeMixin,
    OAuth2ClientMixin,
    OAuth2TokenMixin,
)
from flask import request
from flask_security import AsaList
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, deferred, object_session, relationship

from project import db
from project.dateutils import gmt_tz
from project.models.rate_limit_provider_mixin import (
    RateLimitHolderMixin,
    RateLimitProviderMixin,
)
from project.models.trackable_mixin import TrackableMixin

# OAuth Server: Wir bieten an, dass sich ein Nutzer per OAuth2 auf unserer Seite anmeldet
oauth_refresh_token_expires_in = 90 * 86400  # 90 days


class OAuth2Client(db.Model, OAuth2ClientMixin, RateLimitHolderMixin, TrackableMixin):
    __tablename__ = "oauth2_client"
    __display_name__ = "OAuth2 client"
    __table_args__ = (
        CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name="oauth2_client_admin_unit_xor_user",
        ),
    )
    __default_rate_limit_value__ = "5000/hour"

    id = db.Column(db.Integer, primary_key=True)

    homepage_url = deferred(db.Column(db.String(255)), group="detail")
    setup_url = deferred(db.Column(db.String(255)), group="detail")
    webhook_url = deferred(db.Column(db.String(255)), group="detail")
    webhook_secret = deferred(db.Column(db.Unicode(255)), group="detail")
    description = deferred(db.Column(db.UnicodeText(), nullable=True), group="detail")

    admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )

    app_permissions = db.Column(MutableList.as_mutable(AsaList()), nullable=True)
    app_installations = relationship(
        "AppInstallation",
        primaryjoin="AppInstallation.oauth2_client_id == OAuth2Client.id",
        cascade="all, delete-orphan",
        backref=backref("oauth2_client", lazy=True),
    )
    app_keys = relationship(
        "AppKey",
        cascade="all, delete-orphan",
        backref=backref("oauth2_client", lazy=True),
    )

    @hybrid_property
    def is_app(self):  # pragma: no cover
        return self.app_permissions is not None

    @is_app.expression
    def is_app(cls):
        return cls.app_permissions.isnot(None)

    @OAuth2ClientMixin.grant_types.getter
    def grant_types(self):
        return [
            "authorization_code",
            "refresh_token",
            "client_credentials",
            "urn:ietf:params:oauth:grant-type:jwt-bearer",
        ]

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


class OAuth2Token(db.Model, OAuth2TokenMixin, RateLimitProviderMixin):
    __tablename__ = "oauth2_token"
    __display_name__ = "OAuth2 token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    app_id = db.Column(
        db.Integer, db.ForeignKey("oauth2_client.id", ondelete="CASCADE")
    )
    app = db.relationship("OAuth2Client")

    app_installation_id = db.Column(
        db.Integer, db.ForeignKey("app_installation.id", ondelete="CASCADE")
    )
    app_installation = db.relationship("AppInstallation")

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

    def get_rate_limit_key(self):
        if self.user_id:
            return f"{self.client.get_rate_limit_key()}-{self.user_id}"

        return self.client.get_rate_limit_key()

    def get_rate_limit_value(self):
        return self.client.rate_limit_value
