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
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased, backref, deferred, object_session, relationship
from sqlalchemy.orm.relationships import remote
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.sql.operators import op
from sqlalchemy_utils import ColorType

from project import db
from project.dateutils import gmt_tz
from project.dbtypes import IntegerEnum
from project.utils import make_check_violation

# Base


def create_tsvector(*args):
    field, weight = args[0]
    exp = func.setweight(func.to_tsvector("german", func.coalesce(field, "")), weight)
    for field, weight in args[1:]:
        exp = op(
            exp,
            "||",
            func.setweight(
                func.to_tsvector("german", func.coalesce(field, "")), weight
            ),
        )
    return exp


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
    start_page = Column(UnicodeText())


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
    favorite_events = relationship(
        "Event",
        secondary="user_favoriteevents",
        backref=backref("favored_by_users", lazy=True),
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


class AdminUnitInvitation(db.Model, TrackableMixin):
    __tablename__ = "adminunitinvitation"
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    email = Column(String(255), nullable=False)
    admin_unit_name = Column(String(255))
    relation_auto_verify_event_reference_requests = Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    relation_verify = Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )


class AdminUnitRelation(db.Model, TrackableMixin):
    __tablename__ = "adminunitrelation"
    __table_args__ = (
        UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
        CheckConstraint("source_admin_unit_id != target_admin_unit_id"),
    )
    id = Column(Integer(), primary_key=True)
    source_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    target_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    auto_verify_event_reference_requests = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    verify = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    invited = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )

    def validate(self):
        source_id = (
            self.source_admin_unit.id
            if self.source_admin_unit
            else self.source_admin_unit_id
        )
        target_id = (
            self.target_admin_unit.id
            if self.target_admin_unit
            else self.target_admin_unit_id
        )
        if source_id == target_id:
            raise make_check_violation("There must be no self-reference.")


@listens_for(AdminUnitRelation, "before_insert")
@listens_for(AdminUnitRelation, "before_update")
def before_saving_admin_unit_relation(mapper, connect, self):
    self.validate()


class AdminUnit(db.Model, TrackableMixin):
    __tablename__ = "adminunit"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    short_name = Column(Unicode(100), unique=True)
    members = relationship(
        "AdminUnitMember",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    invitations = relationship(
        "AdminUnitMemberInvitation",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    admin_unit_invitations = relationship(
        "AdminUnitInvitation",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    events = relationship(
        "Event", cascade="all, delete-orphan", backref=backref("admin_unit", lazy=True)
    )
    eventsuggestions = relationship(
        "EventSuggestion",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    references = relationship(
        "EventReference",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    reference_requests = relationship(
        "EventReferenceRequest",
        cascade="all, delete-orphan",
        backref=backref("admin_unit", lazy=True),
    )
    event_organizers = relationship(
        "EventOrganizer",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    event_places = relationship(
        "EventPlace",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    event_lists = relationship(
        "EventList",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
    custom_widgets = relationship(
        "CustomWidget",
        cascade="all, delete-orphan",
        backref=backref("adminunit", lazy=True),
    )
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
    suggestions_enabled = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    can_create_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    can_verify_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    incoming_verification_requests_allowed = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    incoming_verification_requests_text = Column(UnicodeText())
    can_invite_other = deferred(
        Column(
            Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        )
    )
    outgoing_relations = relationship(
        "AdminUnitRelation",
        primaryjoin=remote(AdminUnitRelation.source_admin_unit_id) == id,
        single_parent=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "source_admin_unit",
            lazy=True,
        ),
    )
    incoming_relations = relationship(
        "AdminUnitRelation",
        primaryjoin=remote(AdminUnitRelation.target_admin_unit_id) == id,
        cascade="all, delete-orphan",
        passive_deletes=True,
        backref=backref(
            "target_admin_unit",
            lazy=True,
        ),
    )

    @hybrid_property
    def is_verified(self):
        if not self.incoming_relations:
            return False

        return any(
            r.verify and r.source_admin_unit.can_verify_other
            for r in self.incoming_relations
        )

    @is_verified.expression
    def is_verified(cls):
        SourceAdminUnit = aliased(AdminUnit)

        j = AdminUnitRelation.__table__.join(
            SourceAdminUnit,
            AdminUnitRelation.source_admin_unit_id == SourceAdminUnit.id,
        )
        return (
            select([func.count()])
            .select_from(j)
            .where(
                and_(
                    AdminUnitRelation.verify,
                    AdminUnitRelation.target_admin_unit_id == cls.id,
                    SourceAdminUnit.can_verify_other,
                )
            )
            .as_scalar()
            > 0
        )

    def purge(self):
        if self.logo and self.logo.is_empty():
            self.logo_id = None


@listens_for(AdminUnit, "before_insert")
@listens_for(AdminUnit, "before_update")
def before_saving_admin_unit(mapper, connect, self):
    self.purge()


@listens_for(AdminUnit.can_invite_other, "set")
def set_admin_unit_can_invite_other(target, value, oldvalue, initiator):
    if (
        not value
        and target.admin_unit_invitations
        and len(target.admin_unit_invitations) > 0
    ):
        target.admin_unit_invitations = []


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
    rating = Column(Integer(), default=50)


def sanitize_allday_instance(instance):
    if instance.allday:
        from project.dateutils import date_set_begin_of_day, date_set_end_of_day

        instance.start = date_set_begin_of_day(instance.start)

        if instance.end:
            instance.end = date_set_end_of_day(instance.end)
        else:
            instance.end = date_set_end_of_day(instance.start)


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
    review_status = Column(IntegerEnum(EventReferenceRequestReviewStatus))
    rejection_reason = Column(IntegerEnum(EventReferenceRequestRejectionReason))

    @hybrid_property
    def verified(self):
        return self.review_status == EventReferenceRequestReviewStatus.verified


class EventMixin(object):
    name = Column(Unicode(255), nullable=False)
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
    def __ts_vector__(cls):
        return create_tsvector((cls.name, "A"), (cls.tags, "B"), (cls.description, "C"))

    @declared_attr
    def photo_id(cls):
        return Column("photo_id", ForeignKey("image.id"))

    @declared_attr
    def photo(cls):
        return relationship(
            "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
        )

    def purge_event_mixin(self):
        if self.photo and self.photo.is_empty():
            self.photo_id = None


class EventSuggestion(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "eventsuggestion"
    __table_args__ = (
        CheckConstraint(
            "NOT(event_place_id IS NULL AND event_place_text IS NULL)",
        ),
        CheckConstraint("NOT(organizer_id IS NULL AND organizer_text IS NULL)"),
    )
    id = Column(Integer(), primary_key=True)

    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    recurrence_rule = Column(UnicodeText())

    review_status = Column(IntegerEnum(EventReviewStatus))
    rejection_resaon = Column(IntegerEnum(EventRejectionReason))

    contact_name = Column(Unicode(255), nullable=False)
    contact_email = Column(Unicode(255))
    contact_phone = Column(Unicode(255))
    contact_email_notice = Column(Boolean())

    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)

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
    self.purge_event_mixin()
    sanitize_allday_instance(self)


class Event(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "event"
    id = Column(Integer(), primary_key=True)

    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=False
    )
    organizer = db.relationship("EventOrganizer", uselist=False)
    event_place_id = db.Column(
        db.Integer, db.ForeignKey("eventplace.id"), nullable=False
    )
    event_place = db.relationship("EventPlace", uselist=False)

    categories = relationship("EventCategory", secondary="event_eventcategories")
    co_organizers = relationship(
        "EventOrganizer",
        secondary="event_coorganizers",
        backref=backref("co_organized_events", lazy=True),
    )
    event_lists = relationship(
        "EventList",
        secondary="event_eventlists",
        backref=backref("events", lazy=True),
    )

    public_status = Column(
        IntegerEnum(PublicStatus),
        nullable=False,
        default=PublicStatus.published.value,
        server_default=str(PublicStatus.published.value),
    )
    status = Column(IntegerEnum(EventStatus))
    previous_start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    rating = Column(Integer(), default=50)

    @property
    def min_start_definition(self):
        if self.date_definitions:
            return min(self.date_definitions, key=lambda d: d.start)
        else:
            return None

    @hybrid_property
    def min_start(self):
        if self.date_definitions:
            return min(d.start for d in self.date_definitions)
        else:
            return None

    @min_start.expression
    def min_start(cls):
        return (
            select([EventDateDefinition.start])
            .where(EventDateDefinition.event_id == cls.id)
            .order_by(EventDateDefinition.start)
            .limit(1)
            .as_scalar()
        )

    @hybrid_property
    def is_recurring(self):
        if self.date_definitions:
            return any(d.recurrence_rule for d in self.date_definitions)
        else:
            return False

    @is_recurring.expression
    def is_recurring(cls):
        return (
            select([func.count()])
            .select_from(EventDateDefinition.__table__)
            .where(
                and_(
                    EventDateDefinition.event_id == cls.id,
                    func.coalesce(EventDateDefinition.recurrence_rule, "") != "",
                )
            )
            .as_scalar()
        ) > 0

    date_definitions = relationship(
        "EventDateDefinition",
        order_by="EventDateDefinition.start",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )

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

    @property
    def co_organizer_ids(self):
        return [c.id for c in self.co_organizers]

    @co_organizer_ids.setter
    def co_organizer_ids(self, value):
        self.co_organizers = EventOrganizer.query.filter(
            EventOrganizer.id.in_(value)
        ).all()

    def has_multiple_dates(self) -> bool:
        return self.is_recurring or len(self.date_definitions) > 1

    def is_favored_by_current_user(self) -> bool:
        if not current_user or not current_user.is_authenticated:
            return False

        from project.services.user import has_favorite_event

        return has_favorite_event(current_user.id, self.id)

    def validate(self):
        if self.organizer and self.organizer.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid organizer.")

        if self.co_organizers:
            for co_organizer in self.co_organizers:
                if (
                    co_organizer.admin_unit_id != self.admin_unit_id
                    or co_organizer.id == self.organizer_id
                ):
                    raise make_check_violation("Invalid co-organizer.")

        if self.event_place and self.event_place.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid place.")

        if not self.date_definitions or len(self.date_definitions) == 0:
            raise make_check_violation("At least one date defintion is required.")


@listens_for(Event, "before_insert")
@listens_for(Event, "before_update")
def before_saving_event(mapper, connect, self):
    self.validate()
    self.purge_event_mixin()


class EventDate(db.Model):
    __tablename__ = "eventdate"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    end = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )


@listens_for(EventDate, "before_insert")
@listens_for(EventDate, "before_update")
def purge_event_date(mapper, connect, self):
    sanitize_allday_instance(self)


class EventDateDefinition(db.Model):
    __tablename__ = "eventdatedefinition"
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    recurrence_rule = Column(UnicodeText())

    def validate(self):
        if self.start and self.end:
            if self.start > self.end:
                raise make_check_violation("The start must be before the end.")

            max_end = self.start + relativedelta(days=14)
            if self.end > max_end:
                raise make_check_violation("An event can last a maximum of 14 days.")


@listens_for(EventDateDefinition, "before_insert")
@listens_for(EventDateDefinition, "before_update")
def before_saving_event_date_definition(mapper, connect, self):
    self.validate()
    sanitize_allday_instance(self)


class EventEventCategories(db.Model):
    __tablename__ = "event_eventcategories"
    __table_args__ = (UniqueConstraint("event_id", "category_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )


class EventSuggestionEventCategories(db.Model):
    __tablename__ = "eventsuggestion_eventcategories"
    __table_args__ = (UniqueConstraint("event_suggestion_id", "category_id"),)
    id = Column(Integer(), primary_key=True)
    event_suggestion_id = db.Column(
        db.Integer, db.ForeignKey("eventsuggestion.id"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )


class EventCoOrganizers(db.Model):
    __tablename__ = "event_coorganizers"
    __table_args__ = (UniqueConstraint("event_id", "organizer_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=False
    )


class EventList(db.Model, TrackableMixin):
    __tablename__ = "eventlist"
    __table_args__ = (
        UniqueConstraint(
            "name", "admin_unit_id", name="eventreference_name_admin_unit_id"
        ),
    )
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255))
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)


class EventEventLists(db.Model):
    __tablename__ = "event_eventlists"
    __table_args__ = (UniqueConstraint("event_id", "list_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("eventlist.id"), nullable=False)


class UserFavoriteEvents(db.Model):
    __tablename__ = "user_favoriteevents"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)


class CustomWidget(db.Model, TrackableMixin):
    __tablename__ = "customwidget"
    id = Column(Integer(), primary_key=True)
    widget_type = Column(Unicode(255), nullable=False)
    name = Column(Unicode(255), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    settings = Column(JSONB)


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
