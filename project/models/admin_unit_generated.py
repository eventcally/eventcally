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
from project.models.api_key_owner_mixin import ApiKeyOwnerMixin


class AdminUnitGeneratedMixin(TrackableMixin, ApiKeyOwnerMixin):
    __tablename__ = "adminunit"
    __table_args__ = (
        Index(
            "idx_adminunit_incoming_verification_requests_postal_codes",
            "incoming_verification_requests_postal_codes",
            postgresql_using="gin",
        ),
    )

    __model_name__ = "organization"
    __model_name_plural__ = "organizations"
    __display_name__ = "Organization"
    __display_name_plural__ = "Organizations"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), unique=True, nullable=True)

    @declared_attr
    def short_name(cls):
        return Column(Unicode(100), unique=True, nullable=True)

    @declared_attr
    def deletion_requested_at(cls):
        return deferred(Column(DateTime(), nullable=True), group="deletion")

    @declared_attr
    def url(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def email(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def phone(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def fax(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def description(cls):
        return deferred(Column(UnicodeText(), nullable=True), group="detail")

    @declared_attr
    def widget_font(cls):
        return deferred(Column(Unicode(255), nullable=True), group="widget")

    @declared_attr
    def widget_background_color(cls):
        return deferred(Column(ColorType, nullable=True), group="widget")

    @declared_attr
    def widget_primary_color(cls):
        return deferred(Column(ColorType, nullable=True), group="widget")

    @declared_attr
    def widget_link_color(cls):
        return deferred(Column(ColorType, nullable=True), group="widget")

    @declared_attr
    def incoming_reference_requests_allowed(cls):
        return deferred(Column(Boolean(), nullable=True))

    @declared_attr
    def can_create_other(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def can_verify_other(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def incoming_verification_requests_allowed(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def incoming_verification_requests_text(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def incoming_verification_requests_postal_codes(cls):
        return deferred(
            Column(
                postgresql.ARRAY(Unicode(255)),
                nullable=False,
                default=cast(
                    postgresql.array([], type_=Unicode(255)),
                    postgresql.ARRAY(Unicode(255)),
                ),
                server_default="{}",
            )
        )

    @declared_attr
    def can_invite_other(cls):
        return deferred(
            Column(Boolean(), nullable=False, default=False, server_default="0")
        )

    @declared_attr
    def deletion_requested_by_id(cls):
        return deferred(
            Column(
                Integer(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
            ),
            group="deletion",
        )

    @declared_attr
    def location_id(cls):
        return deferred(
            Column(
                Integer(), ForeignKey("location.id", ondelete="SET NULL"), nullable=True
            )
        )

    @declared_attr
    def logo_id(cls):
        return deferred(
            Column(
                Integer(), ForeignKey("image.id", ondelete="SET NULL"), nullable=True
            )
        )

    @declared_attr
    def deletion_requested_by(cls):
        return relationship(
            "User",
            foreign_keys=[cls.deletion_requested_by_id],
            back_populates="admin_units_deletion_requested",
        )

    @declared_attr
    def members(cls):
        return relationship(
            "AdminUnitMember",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="AdminUnitMember.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def invitations(cls):
        return relationship(
            "AdminUnitMemberInvitation",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="AdminUnitMemberInvitation.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def admin_unit_invitations(cls):
        return relationship(
            "AdminUnitInvitation",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="AdminUnitInvitation.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def events(cls):
        return relationship(
            "Event",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="Event.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def references(cls):
        return relationship(
            "EventReference",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="EventReference.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def reference_requests(cls):
        return relationship(
            "EventReferenceRequest",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="EventReferenceRequest.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def event_organizers(cls):
        return relationship(
            "EventOrganizer",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="EventOrganizer.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def event_places(cls):
        return relationship(
            "EventPlace",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="EventPlace.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def event_lists(cls):
        return relationship(
            "EventList",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="EventList.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def custom_widgets(cls):
        return relationship(
            "CustomWidget",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="CustomWidget.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def location(cls):
        return relationship(
            "Location",
            foreign_keys=[cls.location_id],
            uselist=False,
            single_parent=True,
            cascade="all, delete-orphan",
            back_populates="admin_unit",
        )

    @declared_attr
    def logo(cls):
        return relationship(
            "Image",
            foreign_keys=[cls.logo_id],
            uselist=False,
            single_parent=True,
            cascade="all, delete-orphan",
            back_populates="admin_unit",
        )

    @declared_attr
    def outgoing_relations(cls):
        return relationship(
            "AdminUnitRelation",
            cascade="all, delete-orphan",
            back_populates="source_admin_unit",
            primaryjoin="AdminUnitRelation.source_admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def incoming_relations(cls):
        return relationship(
            "AdminUnitRelation",
            cascade="all, delete-orphan",
            back_populates="target_admin_unit",
            primaryjoin="AdminUnitRelation.target_admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def outgoing_verification_requests(cls):
        return relationship(
            "AdminUnitVerificationRequest",
            cascade="all, delete-orphan",
            back_populates="source_admin_unit",
            primaryjoin="AdminUnitVerificationRequest.source_admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def incoming_verification_requests(cls):
        return relationship(
            "AdminUnitVerificationRequest",
            cascade="all, delete-orphan",
            back_populates="target_admin_unit",
            primaryjoin="AdminUnitVerificationRequest.target_admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def api_keys(cls):
        return relationship(
            "ApiKey",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="ApiKey.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def oauth2_clients(cls):
        return relationship(
            "OAuth2Client",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="OAuth2Client.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def app_installations(cls):
        return relationship(
            "AppInstallation",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="AppInstallation.admin_unit_id == AdminUnit.id",
        )

    @declared_attr
    def app_keys(cls):
        return relationship(
            "AppKey",
            cascade="all, delete-orphan",
            back_populates="admin_unit",
            primaryjoin="AppKey.admin_unit_id == AdminUnit.id",
        )
