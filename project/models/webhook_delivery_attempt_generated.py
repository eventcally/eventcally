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


class WebhookDeliveryAttemptGeneratedMixin:
    __tablename__ = "webhook_delivery_attempt"

    __model_name__ = "webhook_delivery_attempt"
    __model_name_plural__ = "webhook_delivery_attempts"
    __display_name__ = "Webhook delivery attempt"
    __display_name_plural__ = "Webhook delivery attempts"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def url(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def status(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def status_code(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def start_at(cls):
        return Column(DateTime(), nullable=False)

    @declared_attr
    def end_at(cls):
        return Column(DateTime(), nullable=False)

    @declared_attr
    def webhook_delivery_id(cls):
        return Column(
            Integer(),
            ForeignKey("webhook_delivery.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def webhook_delivery(cls):
        return relationship(
            "WebhookDelivery",
            foreign_keys=[cls.webhook_delivery_id],
            back_populates="attempts",
        )
