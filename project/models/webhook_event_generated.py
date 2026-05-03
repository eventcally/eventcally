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


class WebhookEventGeneratedMixin:
    __tablename__ = "webhook_event"

    __model_name__ = "webhook_event"
    __model_name_plural__ = "webhook_events"
    __display_name__ = "Webhook event"
    __display_name_plural__ = "Webhook events"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def timestamp(cls):
        return Column(DateTime(), nullable=False)

    @declared_attr
    def event_type(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def payload(cls):
        return Column(JSONB, nullable=False)

    @declared_attr
    def deliveries(cls):
        return relationship(
            "WebhookDelivery",
            cascade="all, delete-orphan",
            back_populates="webhook_event",
            primaryjoin="WebhookDelivery.webhook_event_id == WebhookEvent.id",
        )
