from enum import IntEnum
from flask_security import AsaList
from geoalchemy2 import Geometry
from project.extensions import db
from sqlalchemy import (
    Index,
    Boolean,
    DateTime,
    Column,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Unicode,
    UniqueConstraint,
    ForeignKey,
    UnicodeText,
    CheckConstraint,
    cast,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, deferred, relationship, remote
from sqlalchemy_utils import ColorType
import datetime
from project.dbtypes import IntegerEnum
from sqlalchemy.ext.declarative import declared_attr


class WebhookDeliveryGeneratedMixin:
    __tablename__ = "webhook_delivery"

    __model_name__ = "webhook_delivery"
    __model_name_plural__ = "webhook_deliveries"
    __display_name__ = "Webhook delivery"
    __display_name_plural__ = "Webhook deliveries"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def webhook_event_id(cls):
        return Column(
            Integer(),
            ForeignKey("webhook_event.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def webhook_id(cls):
        return Column(
            Integer(), ForeignKey("webhook.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def app_installation_id(cls):
        return Column(
            Integer(),
            ForeignKey("app_installation.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def app_id(cls):
        return Column(
            Integer(),
            ForeignKey("oauth2_client.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def attempts(cls):
        return relationship(
            "WebhookDeliveryAttempt",
            cascade="all, delete-orphan",
            back_populates="webhook_delivery",
            primaryjoin="WebhookDeliveryAttempt.webhook_delivery_id == WebhookDelivery.id",
        )

    @declared_attr
    def webhook_event(cls):
        return relationship(
            "WebhookEvent",
            foreign_keys=[cls.webhook_event_id],
            back_populates="deliveries",
        )

    @declared_attr
    def webhook(cls):
        return relationship(
            "Webhook",
            foreign_keys=[cls.webhook_id],
            back_populates="deliveries",
        )

    @declared_attr
    def app_installation(cls):
        return relationship(
            "AppInstallation",
            foreign_keys=[cls.app_installation_id],
            back_populates="webhook_deliveries",
        )

    @declared_attr
    def app(cls):
        return relationship(
            "OAuth2Client",
            foreign_keys=[cls.app_id],
            back_populates="webhook_deliveries",
        )
