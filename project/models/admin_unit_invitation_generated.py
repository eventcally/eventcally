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


class AdminUnitInvitationGeneratedMixin(TrackableMixin):
    __tablename__ = "adminunitinvitation"

    __model_name__ = "organization_invitation"
    __model_name_plural__ = "organization_invitations"
    __display_name__ = "Organization invitation"
    __display_name_plural__ = "Organization invitations"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def email(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def admin_unit_name(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def relation_auto_verify_event_reference_requests(cls):
        return Column(Boolean(), nullable=False, default=False, server_default="0")

    @declared_attr
    def relation_verify(cls):
        return Column(Boolean(), nullable=False, default=False, server_default="0")

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="admin_unit_invitations",
        )
