from app import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey, Unicode, UnicodeText
from flask_security import UserMixin, RoleMixin

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

class Organization(db.Model):
    __tablename__ = 'organization'
    id = Column(Integer(), primary_key=True)
    name = Column(String(255), unique=True)
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

class AdminUnit(db.Model):
    __tablename__ = 'adminunit'
    id = Column(Integer(), primary_key=True)
    name = Column(String(255), unique=True)
    members = relationship('AdminUnitMember', backref=backref('adminunit', lazy=True))
    organizations = relationship('AdminUnitOrg', backref=backref('adminunit', lazy=True))

# Events
class Event(db.Model):
    __tablename__ = 'event'
    id = Column(Integer(), primary_key=True)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey('adminunit.id'), nullable=False)
    admin_unit = db.relationship('AdminUnit', backref=db.backref('events', lazy=True))
    host = Column(Unicode(255), nullable=False) # org|adminunit|string
    #co_hosts: -"-
    #format: real|online
    external_link = Column(String(255))
    #ticket_link = Column(String(255))
    location = Column(Unicode(255), nullable=False) # place|address
    dates = relationship('EventDate', backref=backref('event', lazy=False))
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=False)
    #photo: image(1200x628)
    #category: relationship, nullable=False
    #keywords = Column(String(255)) oder liste?
    #kid_friendly: bool
    verified = Column(Boolean())

# (Multiple Events möglich, wiederholend oder frei, dann aber mit endzeit)
class EventDate(db.Model):
    __tablename__ = 'eventdate'
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    #end: date_time