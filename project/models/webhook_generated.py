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


class WebhookGeneratedMixin:
    __tablename__ = "webhook"
    __table_args__ = (
        Index("idx_webhook_event_types", "event_types", postgresql_using="gin"),
    )

    __model_name__ = "webhook"
    __model_name_plural__ = "webhooks"
    __display_name__ = "Webhook"
    __display_name_plural__ = "Webhooks"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def url(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def secret(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def disabled(cls):
        return Column(Boolean(), nullable=False, default=False, server_default="0")

    @declared_attr
    def event_types(cls):
        return Column(
            postgresql.ARRAY(Unicode(255)),
            nullable=False,
            default=cast(
                postgresql.array([], type_=Unicode(255)), postgresql.ARRAY(Unicode(255))
            ),
            server_default="{}",
        )

    @declared_attr
    def app(cls):
        return relationship(
            "OAuth2Client",
            uselist=False,
            back_populates="webhook",
        )

    @declared_attr
    def deliveries(cls):
        return relationship(
            "WebhookDelivery",
            cascade="all, delete-orphan",
            back_populates="webhook",
            primaryjoin="WebhookDelivery.webhook_id == Webhook.id",
        )
