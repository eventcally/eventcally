from __future__ import annotations

import datetime
import time

from authlib.integrations.sqla_oauth2 import (
    OAuth2AuthorizationCodeMixin,
    OAuth2ClientMixin,
    OAuth2TokenMixin,
)
from flask import request
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session

from project.dateutils import gmt_tz
from project.domain import events
from project.domain.commands.create_app_command import CreateAppCommand
from project.domain.commands.delete_app_command import DeleteAppCommand
from project.domain.commands.update_app_command import UpdateAppCommand
from project.extensions import db
from project.models.mixins.rate_limit_provider_mixin import RateLimitProviderMixin
from project.models.oauth2_authorization_code_generated import (
    OAuth2AuthorizationCodeGeneratedMixin,
)
from project.models.oauth2_client_generated import OAuth2ClientGeneratedMixin
from project.models.oauth2_token_generated import OAuth2TokenGeneratedMixin
from project.utils import update_field_with_command

# OAuth Server: Wir bieten an, dass sich ein Nutzer per OAuth2 auf unserer Seite anmeldet
oauth_refresh_token_expires_in = 90 * 86400  # 90 days


class OAuth2Client(
    db.Model,
    OAuth2ClientGeneratedMixin,
    OAuth2ClientMixin,
):
    __default_rate_limit_value__ = "5000/hour"

    @classmethod
    def create_app(cls, cmd: CreateAppCommand) -> OAuth2Client:
        from project.models import Webhook

        instance = cls()

        instance.admin_unit_id = cmd.admin_unit_id
        instance.description = cmd.description
        instance.app_permissions = cmd.app_permissions
        instance.homepage_url = cmd.homepage_url
        instance.setup_url = cmd.setup_url

        metadata = {
            "client_name": cmd.name,
            "scope": cmd.scope,
            "redirect_uris": cmd.redirect_uris,
        }
        instance.set_client_metadata(metadata)

        event = events.AppCreated(
            actor=cmd.actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
        )

        Webhook.create(cmd.webhook, instance, event, "webhook")

        instance.domain_events.append(event)
        return instance

    def update_app(self, cmd: UpdateAppCommand):
        from project.models import Webhook

        event = events.AppUpdated(
            actor=cmd.actor,
            id=self.id,
            admin_unit_id=self.admin_unit_id,
        )

        self._update_field(cmd, event, "description")
        self._update_field(cmd, event, "app_permissions")
        self._update_field(cmd, event, "homepage_url")
        self._update_field(cmd, event, "setup_url")

        metadata = self.client_metadata or {}
        update_field_with_command(metadata, cmd, event, "client_name", "name", "name")
        update_field_with_command(metadata, cmd, event, "scope")
        update_field_with_command(metadata, cmd, event, "redirect_uris")
        self.set_client_metadata(metadata)

        Webhook.update(cmd.webhook, self, event, "webhook")

        self.domain_events.append(event)

    def delete_app(self, cmd: DeleteAppCommand):
        self.domain_events.append(
            events.AppDeleted(
                actor=cmd.actor, id=self.id, admin_unit_id=self.admin_unit_id
            )
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


class OAuth2AuthorizationCode(
    db.Model, OAuth2AuthorizationCodeGeneratedMixin, OAuth2AuthorizationCodeMixin
):
    pass


class OAuth2Token(
    db.Model, OAuth2TokenGeneratedMixin, OAuth2TokenMixin, RateLimitProviderMixin
):
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
