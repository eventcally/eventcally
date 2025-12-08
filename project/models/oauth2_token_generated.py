from enum import IntEnum
from flask_security import AsaList
from geoalchemy2 import Geometry
from project import db
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


class OAuth2TokenGeneratedMixin:
    __tablename__ = "oauth2_token"

    __model_name__ = "oauth2_token"
    __model_name_plural__ = "oauth2_tokens"
    __display_name__ = "OAuth2 token"
    __display_name_plural__ = "OAuth2 tokens"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def user_id(cls):
        return Column(
            Integer(), ForeignKey("user.id", ondelete="CASCADE"), nullable=True
        )

    @declared_attr
    def app_id(cls):
        return Column(
            Integer(), ForeignKey("oauth2_client.id", ondelete="CASCADE"), nullable=True
        )

    @declared_attr
    def app_installation_id(cls):
        return Column(
            Integer(),
            ForeignKey("app_installation.id", ondelete="CASCADE"),
            nullable=True,
        )

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            foreign_keys=[cls.user_id],
            back_populates="oauth2_tokens",
        )

    @declared_attr
    def app(cls):
        return relationship(
            "OAuth2Client",
            foreign_keys=[cls.app_id],
            back_populates="app_oauth2_tokens",
        )

    @declared_attr
    def app_installation(cls):
        return relationship(
            "AppInstallation",
            foreign_keys=[cls.app_installation_id],
            back_populates="oauth2_tokens",
        )
