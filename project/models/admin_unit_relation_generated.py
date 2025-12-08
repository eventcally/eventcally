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
from project.models.trackable_mixin import TrackableMixin


class AdminUnitRelationGeneratedMixin(TrackableMixin):
    __tablename__ = "adminunitrelation"
    __table_args__ = (
        UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
        CheckConstraint(
            "source_admin_unit_id != target_admin_unit_id", name="source_neq_target"
        ),
    )

    __model_name__ = "organization_relation"
    __model_name_plural__ = "organization_relations"
    __display_name__ = "Organization relation"
    __display_name_plural__ = "Organization relations"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def auto_verify_event_reference_requests(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def verify(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def invited(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def source_admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def target_admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def source_admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.source_admin_unit_id],
            back_populates="outgoing_relations",
        )

    @declared_attr
    def target_admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.target_admin_unit_id],
            back_populates="incoming_relations",
        )
