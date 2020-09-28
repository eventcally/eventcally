from app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.types import TypeDecorator
from sqlalchemy.event import listens_for
from sqlalchemy import UniqueConstraint, Boolean, DateTime, Column, Integer, String, ForeignKey, Unicode, UnicodeText, Numeric, LargeBinary
from flask_security import UserMixin, RoleMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from enum import IntEnum
import datetime
from db import IntegerEnum

### Base

class TrackableMixin(object):
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @declared_attr
    def created_by_id(cls):
        return Column('created_by_id', ForeignKey('user.id'))

    @declared_attr
    def created_by(cls):
        return relationship("User")

### Multi purpose

class Image(db.Model, TrackableMixin):
    __tablename__ = 'image'
    id = Column(Integer(), primary_key=True)
    data = db.Column(db.LargeBinary)
    encoding_format = Column(String(80))

### User

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(UnicodeText())

class User(db.Model, UserMixin):
    __tablename__ = 'user'
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
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')

### Organization

class OrgMemberRolesMembers(db.Model):
    __tablename__ = 'orgmemberroles_members'
    id = Column(Integer(), primary_key=True)
    member_id = Column('member_id', Integer(), ForeignKey('orgmember.id'))
    role_id = Column('role_id', Integer(), ForeignKey('orgmemberrole.id'))

class OrgMemberRole(db.Model, RoleMixin):
    __tablename__ = 'orgmemberrole'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))
    permissions = Column(UnicodeText())

class OrgMember(db.Model):
    __tablename__ = 'orgmember'
    id = Column(Integer(), primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orgmembers', lazy=True))
    roles = relationship('OrgMemberRole', secondary='orgmemberroles_members',
                         backref=backref('members', lazy='dynamic'))

class Organization(db.Model, TrackableMixin):
    __tablename__ = 'organization'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    legal_name = Column(Unicode(255))
    short_name = Column(Unicode(100), unique=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location')
    logo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    logo = db.relationship('Image', uselist=False)
    url = Column(String(255))
    email = Column(Unicode(255))
    phone = Column(Unicode(255))
    fax = Column(Unicode(255))
    members = relationship('OrgMember', backref=backref('organization', lazy=True))

### Admin Unit

class AdminUnitMemberRolesMembers(db.Model):
    __tablename__ = 'adminunitmemberroles_members'
    id = Column(Integer(), primary_key=True)
    member_id = Column('member_id', Integer(), ForeignKey('adminunitmember.id'))
    role_id = Column('role_id', Integer(), ForeignKey('adminunitmemberrole.id'))

class AdminUnitMemberRole(db.Model, RoleMixin):
    __tablename__ = 'adminunitmemberrole'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(UnicodeText())

class AdminUnitMember(db.Model):
    __tablename__ = 'adminunitmember'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('adminunitmembers', lazy=True))
    roles = relationship('AdminUnitMemberRole', secondary='adminunitmemberroles_members',
                         order_by="AdminUnitMemberRole.id",
                         backref=backref('members', lazy='dynamic'))

class AdminUnitMemberInvitation(db.Model):
    __tablename__ = 'adminunitmemberinvitation'
    __table_args__ = (
        UniqueConstraint('email', 'admin_unit_id'),
    )
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    email = Column(String(255))
    roles = Column(UnicodeText())

class AdminUnitOrgRoleOrganizations(db.Model):
    __tablename__ = 'adminunitorgroles_organizations'
    id = Column(Integer(), primary_key=True)
    admin_unit_org_id = Column('admin_unit_org_id', Integer(), ForeignKey('adminunitorg.id'))
    role_id = Column('role_id', Integer(), ForeignKey('adminunitorgrole.id'))

class AdminUnitOrgRole(db.Model, RoleMixin):
    __tablename__ = 'adminunitorgrole'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))
    permissions = Column(UnicodeText())

class AdminUnitOrg(db.Model):
    __tablename__ = 'adminunitorg'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('Organization', backref=db.backref('adminunitorgs', lazy=True))
    roles = relationship('AdminUnitOrgRole', secondary='adminunitorgroles_organizations',
                         backref=backref('organizations', lazy='dynamic'))

class AdminUnit(db.Model, TrackableMixin):
    __tablename__ = 'adminunit'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), unique=True)
    short_name = Column(Unicode(100), unique=True)
    members = relationship('AdminUnitMember', backref=backref('adminunit', lazy=True))
    invitations = relationship('AdminUnitMemberInvitation', backref=backref('adminunit', lazy=True))
    organizations = relationship('AdminUnitOrg', backref=backref('adminunit', lazy=True))
    event_organizers = relationship('EventOrganizer', backref=backref('adminunit', lazy=True))
    event_places = relationship('EventPlace', backref=backref('adminunit', lazy=True))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location')
    logo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    logo = db.relationship('Image', uselist=False)
    url = Column(String(255))
    email = Column(Unicode(255))
    phone = Column(Unicode(255))
    fax = Column(Unicode(255))

# Universal Types

class Actor(db.Model):
    __tablename__ = 'actor'
    __table_args__ = (UniqueConstraint('user_id', 'organization_id', 'admin_unit_id'),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User')
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    organization = db.relationship('Organization')
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'))
    admin_unit = db.relationship('AdminUnit')

class OrgOrAdminUnit(db.Model):
    __tablename__ = 'org_or_adminunit'
    __table_args__ = (
        CheckConstraint('NOT(organization_id IS NULL AND admin_unit_id IS NULL)'),
        UniqueConstraint('organization_id', 'admin_unit_id'),
    )
    id = Column(Integer(), primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    organization = db.relationship('Organization', lazy="joined", backref=backref('org_or_adminunit', cascade="all, delete-orphan", uselist=False, lazy=True))
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'))
    admin_unit = db.relationship('AdminUnit', lazy="joined", backref=backref('org_or_adminunit', cascade="all, delete-orphan", uselist=False, lazy=True))

class Location(db.Model, TrackableMixin):
    __tablename__ = 'location'
    id = Column(Integer(), primary_key=True)
    street = Column(Unicode(255))
    postalCode = Column(Unicode(255))
    city = Column(Unicode(255))
    state = Column(Unicode(255))
    country = Column(Unicode(255))
    latitude = Column(Numeric(18,16))
    longitude = Column(Numeric(19,16))

    def is_empty(self):
        return (not self.street
            and not self.postalCode
            and not self.city
            and not self.state
            and not self.country
            and not self.latitude
            and not self.longitude)

class Place(db.Model, TrackableMixin):
    __tablename__ = 'place'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location', uselist=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    photo = db.relationship('Image', uselist=False)
    url = Column(String(255))
    description = Column(UnicodeText())

    def is_empty(self):
        return (not self.name)

@listens_for(Place, 'before_insert')
@listens_for(Place, 'before_update')
def purge_place(mapper, connect, self):
    if self.location and self.location.is_empty():
        self.location_id = None

# Events
class EventPlace(db.Model, TrackableMixin):
    __tablename__ = 'eventplace'
    __table_args__ = (UniqueConstraint('name', 'organizer_id', 'admin_unit_id'),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location', uselist=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    photo = db.relationship('Image', uselist=False)
    url = Column(String(255))
    description = Column(UnicodeText())
    public = Column(Boolean())
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('eventorganizer.id'), nullable=True)

    def is_empty(self):
        return (not self.name)

@listens_for(EventPlace, 'before_insert')
@listens_for(EventPlace, 'before_update')
def purge_event_place(mapper, connect, self):
    if self.location and self.location.is_empty():
        self.location_id = None

class EventCategory(db.Model):
    __tablename__ = 'eventcategory'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False, unique=True)

class EventSuggestion(db.Model, TrackableMixin):
    __tablename__ = 'eventsuggestion'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    admin_unit = db.relationship('AdminUnit', backref=db.backref('eventsuggestions', lazy=True))
    host_name = Column(Unicode(255), nullable=False)
    event_name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=False)
    place_name = Column(Unicode(255), nullable=False)
    place_street = Column(Unicode(255))
    place_postalCode = Column(Unicode(255), nullable=False)
    place_city = Column(Unicode(255), nullable=False)
    contact_name = Column(Unicode(255), nullable=False)
    contact_email = Column(Unicode(255), nullable=False)
    external_link = Column(String(255))
    dates = relationship('EventSuggestionDate', backref=backref('eventsuggestion', lazy=False), cascade="all, delete-orphan")

class EventSuggestionDate(db.Model):
    __tablename__ = 'eventsuggestiondate'
    id = Column(Integer(), primary_key=True)
    event_suggestion_id = db.Column(db.Integer, db.ForeignKey('eventsuggestion.id'), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    #end: date_time

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

class FeaturedEventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3

class FeaturedEventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4

class EventOrganizer(db.Model, TrackableMixin):
    __tablename__ = 'eventorganizer'
    __table_args__ = (UniqueConstraint('name', 'admin_unit_id'),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    url = Column(String(255))
    email = Column(Unicode(255))
    phone = Column(Unicode(255))
    fax = Column(Unicode(255))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location')
    logo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    logo = db.relationship('Image', uselist=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=True)
    event_places = relationship('EventPlace', backref=backref('organizer', lazy=True))

    def is_empty(self):
        return not self.name

class EventContact(db.Model, TrackableMixin):
    __tablename__ = 'eventcontact'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    email = Column(Unicode(255))
    phone = Column(Unicode(255))

    def is_empty(self):
        return not self.name

class FeaturedEvent(db.Model, TrackableMixin):
    __tablename__ = 'featuredevent'
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    review_status = Column(IntegerEnum(FeaturedEventReviewStatus))
    rejection_resaon = Column(IntegerEnum(FeaturedEventRejectionReason))
    rating = Column(Integer())

class Event(db.Model, TrackableMixin):
    __tablename__ = 'event'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    admin_unit = db.relationship('AdminUnit', backref=db.backref('events', lazy=True))
    organizer_id = db.Column(db.Integer, db.ForeignKey('eventorganizer.id'), nullable=True)
    organizer = db.relationship('EventOrganizer', uselist=False)
    host_id = db.Column(db.Integer, db.ForeignKey('org_or_adminunit.id'), nullable=True)
    host = db.relationship('OrgOrAdminUnit', backref=db.backref('events', lazy=True))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=True)
    place = db.relationship('Place', backref=db.backref('events', lazy=True))
    event_place_id = db.Column(db.Integer, db.ForeignKey('eventplace.id'), nullable=True)
    event_place = db.relationship('EventPlace', uselist=False)
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=False)
    external_link = Column(String(255))
    ticket_link = Column(String(255))

    photo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    photo = db.relationship('Image', uselist=False)
    category_id = db.Column(db.Integer, db.ForeignKey('eventcategory.id'), nullable=False)
    category = relationship('EventCategory', uselist=False)
    tags = Column(UnicodeText())
    kid_friendly = Column(Boolean())
    accessible_for_free = Column(Boolean())
    age_from = Column(Integer())
    age_to = Column(Integer())
    target_group_origin = Column(IntegerEnum(EventTargetGroupOrigin))
    attendance_mode = Column(IntegerEnum(EventAttendanceMode))
    status = Column(IntegerEnum(EventStatus))
    previous_start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    review_status = Column(IntegerEnum(EventReviewStatus))
    rejection_resaon = Column(IntegerEnum(EventRejectionReason))
    rating = Column(Integer())

    @hybrid_property
    def verified(self):
        return self.review_status == EventReviewStatus.verified

    # suggestion
    contact_id = db.Column(db.Integer, db.ForeignKey('eventcontact.id'), nullable=True)
    contact = db.relationship('EventContact', uselist=False)

    recurrence_rule = Column(UnicodeText())
    start = db.Column(db.DateTime(timezone=True), nullable=True)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    dates = relationship('EventDate', backref=backref('event', lazy=False), cascade="all, delete-orphan")

    features = relationship('FeaturedEvent', backref=backref('event', lazy=False), cascade="all, delete-orphan")

@listens_for(Event, 'before_insert')
@listens_for(Event, 'before_update')
def purge_event(mapper, connect, self):
    if self.organizer and self.organizer.is_empty():
        self.organizer_id = None
    if self.event_place and self.event_place.is_empty():
        self.event_place_id = None
    if self.contact and self.contact.is_empty():
        self.contact_id = None

class EventDate(db.Model):
    __tablename__ = 'eventdate'
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)

class Analytics(db.Model):
    __tablename__ = 'analytics'
    id = Column(Integer(), primary_key=True)
    key = Column(Unicode(255))
    value1 = Column(Unicode(255))
    value2 = Column(Unicode(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
