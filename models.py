from app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import CheckConstraint
from sqlalchemy import UniqueConstraint, Boolean, DateTime, Column, Integer, String, ForeignKey, Unicode, UnicodeText, Numeric, LargeBinary
from flask_security import UserMixin, RoleMixin
import datetime

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
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location')
    logo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    logo = db.relationship('Image', uselist=False)
    url = Column(String(255))
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
    description = Column(String(255))
    permissions = Column(UnicodeText())

class AdminUnitMember(db.Model):
    __tablename__ = 'adminunitmember'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('adminunitmembers', lazy=True))
    roles = relationship('AdminUnitMemberRole', secondary='adminunitmemberroles_members',
                         backref=backref('members', lazy='dynamic'))

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
    members = relationship('AdminUnitMember', backref=backref('adminunit', lazy=True))
    organizations = relationship('AdminUnitOrg', backref=backref('adminunit', lazy=True))

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

class Place(db.Model, TrackableMixin):
    __tablename__ = 'place'
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False, unique=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location')
    photo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    photo = db.relationship('Image', uselist=False)
    url = Column(String(255))
    description = Column(UnicodeText())

# Events
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

class Event(db.Model, TrackableMixin):
    __tablename__ = 'event'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    admin_unit = db.relationship('AdminUnit', backref=db.backref('events', lazy=True))
    host_id = db.Column(db.Integer, db.ForeignKey('org_or_adminunit.id'), nullable=False)
    host = db.relationship('OrgOrAdminUnit', backref=db.backref('events', lazy=True))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    place = db.relationship('Place', backref=db.backref('events', lazy=True))
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=False)
    external_link = Column(String(255))
    ticket_link = Column(String(255))
    verified = Column(Boolean())
    photo_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    photo = db.relationship('Image', uselist=False)
    category_id = db.Column(db.Integer, db.ForeignKey('eventcategory.id'))
    category = relationship('EventCategory', uselist=False)

    dates = relationship('EventDate', backref=backref('event', lazy=False), cascade="all, delete-orphan")
    # wiederkehrende Dates sind zeitlich eingeschränkt
    # beim event müsste man dann auch nochmal start_time (nullable=False) und end_time machen.
    #keywords/tags = Column(String(255)) oder liste?
    #kid_friendly: bool
    # target_group:
    #     age_from: int
    #     age_to: int
    #     mainly_for_tourists: bool
    #
    #
    # = kärnten =
    # eventSchedules: RepeatFrequency (wiederkehrende Beschreibung, keine konkreten Daten)
    # allDay: bool
    # status: Scheduled (Default), Cancelled, MovedOnline, Postponed, Rescheduled
    # previousStartDates: DateTime (see status)
    # attendanceMode: Offline, Online, Mixed
    # isAccessibleForFree: bool
    # typicalAgeRange: string (9-99)

# (Multiple Events möglich, wiederholend oder frei, dann aber mit endzeit)
# Facebook Limitations:
# An event can't last longer than a day
# An event can't span more than 52 weeks
# Each event can have a max of 52 instances
# Once the event has begun, you can't add instances totaling more than 52 weeks after the initial start date
class EventDate(db.Model):
    __tablename__ = 'eventdate'
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    #end: date_time