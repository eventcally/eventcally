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


class OAuth2AuthorizationCodeGeneratedMixin:
    __tablename__ = "oauth2_code"

    __model_name__ = "oauth2_authorization_code"
    __model_name_plural__ = "oauth2_authorization_codes"
    __display_name__ = "Oauth2 authorization code"
    __display_name_plural__ = "Oauth2 authorization codes"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def user_id(cls):
        return Column(
            Integer(), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            foreign_keys=[cls.user_id],
            back_populates="oauth2_authorization_codes",
        )
