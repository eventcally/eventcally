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
from project.actor import current_actor


class TrackableGeneratedMixin:

    @declared_attr
    def created_at(cls):
        return deferred(
            Column(DateTime(), default=datetime.datetime.utcnow, nullable=True),
            group="trackable",
        )

    @declared_attr
    def updated_at(cls):
        return deferred(
            Column(DateTime(), onupdate=datetime.datetime.utcnow, nullable=True),
            group="trackable",
        )

    @declared_attr
    def created_by_id(cls):
        return deferred(
            Column(
                Integer(),
                ForeignKey("user.id", ondelete="SET NULL"),
                nullable=True,
                default=current_actor.current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by_id(cls):
        return deferred(
            Column(
                Integer(),
                ForeignKey("user.id", ondelete="SET NULL"),
                nullable=True,
                onupdate=current_actor.current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by_app_installation_id(cls):
        return deferred(
            Column(
                Integer(),
                ForeignKey("app_installation.id", ondelete="SET NULL"),
                nullable=True,
                default=current_actor.current_app_installation_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by_app_installation_id(cls):
        return deferred(
            Column(
                Integer(),
                ForeignKey("app_installation.id", ondelete="SET NULL"),
                nullable=True,
                onupdate=current_actor.current_app_installation_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by(cls):
        return relationship(
            "User",
            foreign_keys=[cls.created_by_id],
        )

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User",
            foreign_keys=[cls.updated_by_id],
        )

    @declared_attr
    def created_by_app_installation(cls):
        return relationship(
            "AppInstallation",
            foreign_keys=[cls.created_by_app_installation_id],
        )

    @declared_attr
    def updated_by_app_installation(cls):
        return relationship(
            "AppInstallation",
            foreign_keys=[cls.updated_by_app_installation_id],
        )
