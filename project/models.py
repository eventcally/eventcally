import datetime
import time
from enum import IntEnum

from authlib.integrations.sqla_oauth2 import (
    OAuth2AuthorizationCodeMixin,
    OAuth2ClientMixin,
    OAuth2TokenMixin,
)
from dateutil.relativedelta import relativedelta
from flask import request
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_security import RoleMixin, UserMixin, current_user
from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    and_,
)
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, deferred, object_session, relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy_utils import ColorType

from project import db
from project.dateutils import gmt_tz
from project.dbtypes import IntegerEnum
from project.utils import make_check_violation

# Base


def _current_user_id_or_none():
    if current_user and current_user.is_authenticated:
        return current_user.id

    return None


class TrackableMixin(object):
    @declared_attr
    def created_at(cls):
        return deferred(
            Column(DateTime, default=datetime.datetime.utcnow), group="trackable"
        )

    @declared_attr
    def updated_at(cls):
        return deferred(
            Column(
                DateTime,
                default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by_id(cls):
        return deferred(
            Column(
                "created_by_id",
                ForeignKey("user.id"),
                default=_current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def created_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.created_by_id" % cls.__name__,
            remote_side="User.id",
        )

    @declared_attr
    def updated_by_id(cls):
        return deferred(
            Column(
                "updated_by_id",
                ForeignKey("user.id"),
                default=_current_user_id_or_none,
                onupdate=_current_user_id_or_none,
            ),
            group="trackable",
        )

    @declared_attr
    def updated_by(cls):
        return relationship(
            "User",
            primaryjoin="User.id == %s.updated_by_id" % cls.__name__,
            remote_side="User.id",
        )


# Global


class Settings(db.Model, TrackableMixin):
    __tablename__ = "settings"
    id = Column(Integer(), primary_key=True)
    tos = Column(UnicodeText())
    legal_notice = Column(UnicodeText())
    contact = Column(UnicodeText())
    privacy = Column(UnicodeText())


# Multi purpose


class Image(db.Model, TrackableMixin):
    __tablename__ = "image"
    id = Column(Integer(), primary_key=True)
    data = deferred(db.Column(db.LargeBinary))
    encoding_format = Column(String(80))
    copyright_text = Column(Unicode(255))

    def is_empty(self):
        return not self.data

    def get_hash(self):
        return (
            int(self.updated_at.replace(tzinfo=gmt_tz).timestamp() * 1000)
            if self.updated_at
            else 0
        )


# User


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = Column(Integer(), primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey("user.id"))
    role_id = Column("role_id", Integer(), ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(UnicodeText())


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    fs_uniquifier = Column(String(255))
    confirmed_at = Column(DateTime())
    roles = relationship(
        "Role", secondary="roles_users", backref=backref("users", lazy="dynamic")
    )

    def get_user_id(self):
        return self.id


# OAuth Consumer: Wenn wir OAuth consumen und sich ein Nutzer per Google oder Facebook anmelden möchte


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")


# OAuth Server: Wir bieten an, dass sich ein Nutzer per OAuth2 auf unserer Seite anmeldet


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = "oauth2_client"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    @OAuth2ClientMixin.grant_types.getter
    def grant_types(self):
        return ["authorization_code", "refresh_token"]

    @OAuth2ClientMixin.response_types.getter
    def response_types(self):
        return ["code"]

    @OAuth2ClientMixin.token_endpoint_auth_method.getter
    def token_endpoint_auth_method(self):
        return ["client_secret_basic", "client_secret_post", "none"]

    def check_redirect_uri(self, redirect_uri):
        if redirect_uri.startswith(request.host_url):  # pragma: no cover
            return True

        return super().check_redirect_uri(redirect_uri)

    def check_token_endpoint_auth_method(self, method):
        return method in self.token_endpoint_auth_method


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_code"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = "oauth2_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User")

    @property
    def client(self):
        return (
            object_session(self)
            .query(OAuth2Client)
            .filter(OAuth2Client.client_id == self.client_id)
            .first()
        )

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()


# Admin Unit


class AdminUnitMemberRolesMembers(db.Model):
    __tablename__ = "adminunitmemberroles_members"
    id = Column(Integer(), primary_key=True)
    member_id = Column("member_id", Integer(), ForeignKey("adminunitmember.id"))
    role_id = Column("role_id", Integer(), ForeignKey("adminunitmemberrole.id"))


class AdminUnitMemberRole(db.Model, RoleMixin):
    __tablename__ = "adminunitmemberrole"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(UnicodeText())


class AdminUnitMember(db.Model):
    __tablename__ = "adminunitmember"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("adminunitmembers", lazy=True))
    roles = relationship(
        "AdminUnitMemberRole",
        secondary="adminunitmemberroles_members",
        order_by="AdminUnitMemberRole.id",
        backref=backref("members", lazy="dynamic"),
    )


class AdminUnitMemberInvitation(db.Model):
    __tablename__ = "adminunitmemberinvitation"
    __table_args__ = (UniqueConstraint("email", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    email = Column(String(255))
    roles = Column(UnicodeText())


class AdminUnit(db.Model, TrackableMixin):
    __tablename__ = "adminunit"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    short_name = Column(Unicode(100), unique=True)
    members = relationship("AdminUnitMember", backref=backref("adminunit", lazy=True))
    invitations = relationship(
        "AdminUnitMemberInvitation", backref=backref("adminunit", lazy=True)
    )
    event_organizers = relationship(
        "EventOrganizer", backref=backref("adminunit", lazy=True)
    )
    event_places = relationship("EventPlace", backref=backref("adminunit", lazy=True))
    location_id = deferred(db.Column(db.Integer, db.ForeignKey("location.id")))
    location = db.relationship(
        "Location", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    logo_id = deferred(db.Column(db.Integer, db.ForeignKey("image.id")))
    logo = db.relationship(
        "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    url = deferred(Column(String(255)), group="detail")
    email = deferred(Column(Unicode(255)), group="detail")
    phone = deferred(Column(Unicode(255)), group="detail")
    fax = deferred(Column(Unicode(255)), group="detail")
    widget_font = deferred(Column(Unicode(255)), group="widget")
    widget_background_color = deferred(Column(ColorType), group="widget")
    widget_primary_color = deferred(Column(ColorType), group="widget")
    widget_link_color = deferred(Column(ColorType), group="widget")
    incoming_reference_requests_allowed = deferred(Column(Boolean()))


@listens_for(AdminUnit, "before_insert")
@listens_for(AdminUnit, "before_update")
def purge_admin_unit(mapper, connect, self):
    if self.logo and self.logo.is_empty():
        self.logo_id = None


# Universal Types


class Location(db.Model, TrackableMixin):
    __tablename__ = "location"
    id = Column(Integer(), primary_key=True)
    street = Column(Unicode(255))
    postalCode = Column(Unicode(255))
    city = Column(Unicode(255))
    state = Column(Unicode(255))
    country = Column(Unicode(255))
    latitude = Column(Numeric(18, 16))
    longitude = Column(Numeric(19, 16))
    coordinate = Column(Geometry(geometry_type="POINT"))

    def __init__(self, **kwargs):
        super(Location, self).__init__(**kwargs)

    def is_empty(self):
        return (
            not self.street
            and not self.postalCode
            and not self.city
            and not self.state
            and not self.country
            and not self.latitude
            and not self.longitude
        )

    def update_coordinate(self):
        if self.latitude and self.longitude:
            point = "POINT({} {})".format(self.longitude, self.latitude)
            self.coordinate = point
        else:
            self.coordinate = None

    @classmethod
    def update_coordinates(cls):
        locations = Location.query.filter(
            and_(
                Location.latitude is not None,
                Location.latitude != 0,
                Location.coordinate is None,
            )
        ).all()

        for location in locations:  # pragma: no cover
            location.update_coordinate()

        db.session.commit()


@listens_for(Location, "before_insert")
@listens_for(Location, "before_update")
def update_location_coordinate(mapper, connect, self):
    self.update_coordinate()


# Events
class EventPlace(db.Model, TrackableMixin):
    __tablename__ = "eventplace"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    location = db.relationship(
        "Location", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    photo_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    photo = db.relationship(
        "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    url = Column(String(255))
    description = Column(UnicodeText())
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=True)


@listens_for(EventPlace, "before_insert")
@listens_for(EventPlace, "before_update")
def purge_event_place(mapper, connect, self):
    if self.location and self.location.is_empty():
        self.location_id = None
    if self.photo and self.photo.is_empty():
        self.photo_id = None


class EventCategory(db.Model):
    __tablename__ = "eventcategory"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False, unique=True)


class EventTargetGroupOrigin(IntEnum):
    both = 1
    tourist = 2
    resident = 3


class EventAttendanceMode(IntEnum):
    offline = 1
    online = 2
    mixed = 3


class EventStatus(IntEnum):
    scheduled = 1
    cancelled = 2
    movedOnline = 3
    postponed = 4
    rescheduled = 5


class EventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3


class EventReferenceRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventReferenceRequestRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4


class PublicStatus(IntEnum):
    draft = 1
    published = 2


class EventOrganizer(db.Model, TrackableMixin):
    __tablename__ = "eventorganizer"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    url = deferred(Column(String(255)), group="detail")
    email = deferred(Column(Unicode(255)), group="detail")
    phone = deferred(Column(Unicode(255)), group="detail")
    fax = deferred(Column(Unicode(255)), group="detail")
    location_id = deferred(db.Column(db.Integer, db.ForeignKey("location.id")))
    location = db.relationship(
        "Location", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    logo_id = deferred(db.Column(db.Integer, db.ForeignKey("image.id")))
    logo = db.relationship(
        "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=True)


@listens_for(EventOrganizer, "before_insert")
@listens_for(EventOrganizer, "before_update")
def purge_event_organizer(mapper, connect, self):
    if self.logo and self.logo.is_empty():
        self.logo_id = None


class EventReference(db.Model, TrackableMixin):
    __tablename__ = "eventreference"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "admin_unit_id", name="eventreference_event_id_admin_unit_id"
        ),
    )
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    admin_unit = db.relationship(
        "AdminUnit", backref=db.backref("references", lazy=True)
    )
    rating = Column(Integer())


class EventReferenceRequest(db.Model, TrackableMixin):
    __tablename__ = "eventreferencerequest"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "admin_unit_id",
            name="eventreferencerequest_event_id_admin_unit_id",
        ),
    )
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    admin_unit = db.relationship(
        "AdminUnit", backref=db.backref("reference_requests", lazy=True)
    )
    review_status = Column(IntegerEnum(EventReferenceRequestReviewStatus))
    rejection_reason = Column(IntegerEnum(EventReferenceRequestRejectionReason))

    @hybrid_property
    def verified(self):
        return self.review_status == EventReferenceRequestReviewStatus.verified


class EventMixin(object):
    name = Column(Unicode(255), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    recurrence_rule = Column(UnicodeText())
    external_link = Column(String(255))
    description = Column(UnicodeText(), nullable=True)

    ticket_link = Column(String(255))
    tags = Column(UnicodeText())
    kid_friendly = Column(Boolean())
    accessible_for_free = Column(Boolean())
    age_from = Column(Integer())
    age_to = Column(Integer())
    target_group_origin = Column(IntegerEnum(EventTargetGroupOrigin))
    attendance_mode = Column(IntegerEnum(EventAttendanceMode))
    registration_required = Column(Boolean())
    booked_up = Column(Boolean())
    expected_participants = Column(Integer())
    price_info = Column(UnicodeText())

    @declared_attr
    def photo_id(cls):
        return Column("photo_id", ForeignKey("image.id"))

    @declared_attr
    def photo(cls):
        return relationship(
            "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
        )


class EventSuggestion(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "eventsuggestion"
    __table_args__ = (
        CheckConstraint(
            "NOT(event_place_id IS NULL AND event_place_text IS NULL)",
        ),
        CheckConstraint("NOT(organizer_id IS NULL AND organizer_text IS NULL)"),
    )
    id = Column(Integer(), primary_key=True)

    review_status = Column(IntegerEnum(EventReviewStatus))
    rejection_resaon = Column(IntegerEnum(EventRejectionReason))

    contact_name = Column(Unicode(255), nullable=False)
    contact_email = Column(Unicode(255))
    contact_phone = Column(Unicode(255))
    contact_email_notice = Column(Boolean())

    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    admin_unit = db.relationship(
        "AdminUnit", backref=db.backref("eventsuggestions", lazy=True)
    )

    event_place_id = db.Column(
        db.Integer, db.ForeignKey("eventplace.id"), nullable=True
    )
    event_place = db.relationship("EventPlace", uselist=False)
    event_place_text = Column(Unicode(255), nullable=True)

    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=True
    )
    organizer = db.relationship("EventOrganizer", uselist=False)
    organizer_text = Column(Unicode(255), nullable=True)

    categories = relationship(
        "EventCategory", secondary="eventsuggestion_eventcategories"
    )

    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="SET NULL"), nullable=True
    )
    event = db.relationship("Event", uselist=False)

    @hybrid_property
    def verified(self):
        return self.review_status == EventReviewStatus.verified


@listens_for(EventSuggestion, "before_insert")
@listens_for(EventSuggestion, "before_update")
def purge_event_suggestion(mapper, connect, self):
    if self.organizer_id is not None:
        self.organizer_text = None
    if self.event_place_id is not None:
        self.event_place_text = None
    if self.photo and self.photo.is_empty():
        self.photo_id = None


class Event(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "event"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    admin_unit = db.relationship("AdminUnit", backref=db.backref("events", lazy=True))
    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=False
    )
    organizer = db.relationship("EventOrganizer", uselist=False)
    event_place_id = db.Column(
        db.Integer, db.ForeignKey("eventplace.id"), nullable=False
    )
    event_place = db.relationship("EventPlace", uselist=False)

    categories = relationship("EventCategory", secondary="event_eventcategories")

    public_status = Column(
        IntegerEnum(PublicStatus),
        nullable=False,
        default=PublicStatus.published.value,
        server_default=str(PublicStatus.published.value),
    )
    status = Column(IntegerEnum(EventStatus))
    previous_start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    rating = Column(Integer())

    dates = relationship(
        "EventDate", backref=backref("event", lazy=False), cascade="all, delete-orphan"
    )

    references = relationship(
        "EventReference",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )
    reference_requests = relationship(
        "EventReferenceRequest",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def category(self):
        if self.categories:
            return self.categories[0]
        else:
            return None

    def validate(self):
        if self.organizer and self.organizer.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid organizer")

        if self.event_place and self.event_place.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid place")

        if self.start and self.end:
            if self.start > self.end:
                raise make_check_violation("The start must be before the end.")

            max_end = self.start + relativedelta(days=14)
            if self.end > max_end:
                raise make_check_violation("An event can last a maximum of 14 days.")


@listens_for(Event, "before_insert")
@listens_for(Event, "before_update")
def purge_event(mapper, connect, self):
    if self.photo and self.photo.is_empty():
        self.photo_id = None


class EventDate(db.Model):
    __tablename__ = "eventdate"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    end = db.Column(db.DateTime(timezone=True), nullable=True, index=True)


class EventEventCategories(db.Model):
    __tablename__ = "event_eventcategories"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )


class EventSuggestionEventCategories(db.Model):
    __tablename__ = "eventsuggestion_eventcategories"
    id = Column(Integer(), primary_key=True)
    event_suggestion_id = db.Column(
        db.Integer, db.ForeignKey("eventsuggestion.id"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )


class Analytics(db.Model):
    __tablename__ = "analytics"
    id = Column(Integer(), primary_key=True)
    key = Column(Unicode(255))
    value1 = Column(Unicode(255))
    value2 = Column(Unicode(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Deprecated begin
class FeaturedEventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class FeaturedEventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4


# Deprecated end
