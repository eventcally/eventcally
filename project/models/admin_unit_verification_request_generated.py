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
from project.models.mixins.trackable_mixin import TrackableMixin


class AdminUnitVerificationRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class AdminUnitVerificationRequestRejectionReason(IntEnum):
    notresponsible = 1
    missinginformation = 2
    unknown = 3
    untrustworthy = 4
    illegal = 5
    irrelevant = 6


class AdminUnitVerificationRequestGeneratedMixin(TrackableMixin):
    __tablename__ = "adminunitverificationrequest"
    __table_args__ = (
        UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
        CheckConstraint(
            "source_admin_unit_id != target_admin_unit_id",
            name="auvr_source_neq_target",
        ),
    )

    __model_name__ = "organization_verification_request"
    __model_name_plural__ = "organization_verification_requests"
    __display_name__ = "Organization verification request"
    __display_name_plural__ = "Organization verification requests"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def review_status(cls):
        return Column(
            IntegerEnum(AdminUnitVerificationRequestReviewStatus), nullable=True
        )

    @declared_attr
    def rejection_reason(cls):
        return Column(
            IntegerEnum(AdminUnitVerificationRequestRejectionReason), nullable=True
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
            back_populates="outgoing_verification_requests",
        )

    @declared_attr
    def target_admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.target_admin_unit_id],
            back_populates="incoming_verification_requests",
        )
