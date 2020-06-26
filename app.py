import os
from base64 import b64decode
from flask import Flask, render_template, request, url_for, redirect, abort, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import asc, func
from flask_security import Security, current_user, auth_required, roles_required, hash_password, SQLAlchemySessionUserDatastore
from flask_security.utils import FsPermNeed
from flask_babelex import Babel, gettext, lazy_gettext, format_datetime
from flask_principal import Permission
from datetime import datetime
import pytz
from urllib.parse import quote_plus
from dateutil.rrule import rrulestr, rruleset, rrule

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['LANGUAGES'] = ['en', 'de']

# Generate a nice key using secrets.token_urlsafe()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')

# i18n
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Berlin'
babel = Babel(app)

app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)

# create db
db = SQLAlchemy(app)

# Setup Flask-Security
# Define models
from models import EventCategory, Image, EventSuggestion, EventSuggestionDate, OrgOrAdminUnit, Actor, Place, Location, User, Role, AdminUnit, AdminUnitMember, AdminUnitMemberRole, OrgMember, OrgMemberRole, Organization, AdminUnitOrg, AdminUnitOrgRole, Event, EventDate
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

berlin_tz = pytz.timezone('Europe/Berlin')
now = datetime.now(tz=berlin_tz)
today = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

def get_event_category_name(category):
    return lazy_gettext('Event_' + category.name)

app.jinja_env.filters['event_category_name'] = lambda u: get_event_category_name(u)

def print_dynamic_texts():
    gettext('Event_Art')
    gettext('Event_Book')
    gettext('Event_Movie')
    gettext('Event_Family')
    gettext('Event_Festival')
    gettext('Event_Religious')
    gettext('Event_Shopping')
    gettext('Event_Comedy')
    gettext('Event_Music')
    gettext('Event_Dance')
    gettext('Event_Nightlife')
    gettext('Event_Theater')
    gettext('Event_Dining')
    gettext('Event_Conference')
    gettext('Event_Meetup')
    gettext('Event_Fitness')
    gettext('Event_Sports')
    gettext('Event_Other')

def get_img_resource(res):
    with current_app.open_resource('static/img/' + res) as f:
        return f.read()

# Create a user to test with
def upsert_user(email, password="password"):
    result = user_datastore.find_user(email=email)
    if result is None:
        result = user_datastore.create_user(email=email, password=hash_password(password))
    return result

def upsert_admin_unit(unit_name):
    admin_unit = AdminUnit.query.filter_by(name = unit_name).first()
    if admin_unit is None:
        admin_unit = AdminUnit(name = unit_name)
        db.session.add(admin_unit)

    upsert_org_or_admin_unit_for_admin_unit(admin_unit)
    return admin_unit

def get_admin_unit(unit_name):
    return AdminUnit.query.filter_by(name = unit_name).first()

def upsert_org_member_role(role_name, permissions):
    result = OrgMemberRole.query.filter_by(name = role_name).first()
    if result is None:
        result = OrgMemberRole(name = role_name)
        db.session.add(result)

    result.remove_permissions(result.get_permissions())
    result.add_permissions(permissions)
    return result

def upsert_admin_unit_member_role(role_name, permissions):
    result = AdminUnitMemberRole.query.filter_by(name = role_name).first()
    if result is None:
        result = AdminUnitMemberRole(name = role_name)
        db.session.add(result)

    result.remove_permissions(result.get_permissions())
    result.add_permissions(permissions)
    return result

def upsert_admin_unit_org_role(role_name, permissions):
    result = AdminUnitOrgRole.query.filter_by(name = role_name).first()
    if result is None:
        result = AdminUnitOrgRole(name = role_name)
        db.session.add(result)

    result.remove_permissions(result.get_permissions())
    result.add_permissions(permissions)
    return result

def add_user_to_organization(user, organization):
    result = OrgMember.query.with_parent(organization).filter_by(user_id = user.id).first()
    if result is None:
        result = OrgMember(user = user, organization_id = organization.id)
        organization.members.append(result)
        db.session.add(result)
    return result

def add_user_to_admin_unit(user, admin_unit):
    result = OrgMember.query.with_parent(admin_unit).filter_by(user_id = user.id).first()
    if result is None:
        result = OrgMember(user = user)
        admin_unit.members.append(result)
        db.session.add(result)
    return result

def add_user_to_admin_unit(user, admin_unit):
    result = AdminUnitMember.query.with_parent(admin_unit).filter_by(user_id = user.id).first()
    if result is None:
        result = AdminUnitMember(user = user, admin_unit_id=admin_unit.id)
        admin_unit.members.append(result)
        db.session.add(result)
    return result

def add_organization_to_admin_unit(organization, admin_unit):
    result = AdminUnitOrg.query.with_parent(admin_unit).filter_by(organization_id = organization.id).first()
    if result is None:
        result = AdminUnitOrg(organization = organization, admin_unit_id=admin_unit.id)
        admin_unit.organizations.append(result)
        db.session.add(result)
    return result

def add_role_to_admin_unit_org(admin_unit_org, role):
    if AdminUnitOrgRole.query.with_parent(admin_unit_org).filter_by(name = role.name).first() is None:
        admin_unit_org.roles.append(role)

def add_role_to_admin_unit_member(admin_unit_member, role):
    if AdminUnitMemberRole.query.with_parent(admin_unit_member).filter_by(name = role.name).first() is None:
        admin_unit_member.roles.append(role)

def add_role_to_org_member(org_member, role):
    if OrgMemberRole.query.with_parent(org_member).filter_by(name = role.name).first() is None:
        org_member.roles.append(role)

def upsert_image_with_data(image, data, encoding_format = "image/jpeg"):
    if image is None:
        image = Image()

    image.data = data
    image.encoding_format = encoding_format

    return image

def upsert_image_with_res(image, res):
    if image is None:
        image = Image()

    image.data = get_img_resource(res)
    image.encoding_format = "image/jpeg"

    return image

def upsert_organization(org_name, street = None, postalCode = None, city = None, latitude = 0, longitude = 0, legal_name = None, url=None, logo_res=None):
    result = Organization.query.filter_by(name = org_name).first()
    if result is None:
        result = Organization(name = org_name)
        db.session.add(result)

    result.legal_name = legal_name
    result.url = url

    if city is not None:
        result.location = upsert_location(street, postalCode, city, latitude, longitude)

    if logo_res is not None:
        result.logo = upsert_image_with_res(result.logo, logo_res)

    upsert_org_or_admin_unit_for_organization(result)
    return result

def create_berlin_date(year, month, day, hour, minute = 0):
    return berlin_tz.localize(datetime(year, month, day, hour=hour, minute=minute))

def upsert_actor_for_admin_unit(admin_unit_id):
    result = Actor.query.filter_by(admin_unit_id = admin_unit_id).first()
    if result is None:
        result = Actor(admin_unit_id = admin_unit_id)
        db.session.add(result)
    return result

def upsert_org_or_admin_unit_for_admin_unit(admin_unit):
    result = OrgOrAdminUnit.query.filter_by(admin_unit = admin_unit).first()
    if result is None:
        result = OrgOrAdminUnit(admin_unit = admin_unit)
        db.session.add(result)
    return result

def upsert_org_or_admin_unit_for_organization(organization):
    result = OrgOrAdminUnit.query.filter_by(organization = organization).first()
    if result is None:
        result = OrgOrAdminUnit(organization = organization)
        db.session.add(result)
    return result

def upsert_location(street, postalCode, city, latitude = 0, longitude = 0):
    result = Location.query.filter_by(street = street, postalCode=postalCode, city=city).first()
    if result is None:
        result = Location(street = street, postalCode=postalCode, city=city)
        db.session.add(result)

    result.latitude = latitude
    result.longitude = longitude

    return result

def upsert_place(name, street = None, postalCode = None, city = None, latitude = 0, longitude = 0, url=None, description=None, photo_res=None):
    result = Place.query.filter_by(name = name).first()
    if result is None:
        result = Place(name = name)
        db.session.add(result)

    if url:
        result.url=url

    if description:
        result.description=description

    if city is not None:
        result.location = upsert_location(street, postalCode, city, latitude, longitude)

    if photo_res is not None:
        result.photo = upsert_image_with_res(result.photo, photo_res)

    return result

def upsert_event_suggestion(event_name, host_name, place_name, start, description, link = None, admin_unit = None):
    if admin_unit is None:
        admin_unit = get_admin_unit('Stadt Goslar')

    result = EventSuggestion.query.filter_by(event_name = event_name).first()
    if result is None:
        result = EventSuggestion()
        db.session.add(result)

    result.admin_unit = admin_unit
    result.event_name = event_name
    result.description = description
    result.external_link = link
    result.place_name = place_name
    result.host_name = host_name

    result.place_postalCode = "Dummy postal code"
    result.place_city = "Dummy city"
    result.contact_name = "Dummy contact name"
    result.contact_email = "Dummy contact email"

    eventDate = EventSuggestionDate(event_suggestion_id = result.id, start=start)
    result.dates = []
    result.dates.append(eventDate)

    return result

def upsert_event_category(category_name):
    result = EventCategory.query.filter_by(name = category_name).first()
    if result is None:
        result = EventCategory(name = category_name)
        db.session.add(result)

    return result

def upsert_event(event_name, host, location_name, start, description, link = None, verified = False, admin_unit = None, ticket_link=None, photo_res=None, category=None, recurrence_rule=None):
    if admin_unit is None:
        admin_unit = get_admin_unit('Stadt Goslar')
    place = upsert_place(location_name)

    if category is not None:
        category_object = upsert_event_category(category)
    else:
        category_object = upsert_event_category('Other')

    result = Event.query.filter_by(name = event_name).first()
    if result is None:
        result = Event()
        db.session.add(result)

    result.name = event_name
    result.description = description
    result.external_link = link
    result.verified = verified
    result.admin_unit = admin_unit
    result.host = host
    result.place = place
    result.ticket_link = ticket_link
    result.category = category_object

    result.dates = []

    if recurrence_rule is not None:
        result.recurrence_rule = recurrence_rule
        start_wo_tz = start.replace(tzinfo=None)
        rule_set = rrulestr(recurrence_rule, forceset=True, dtstart=start_wo_tz)
        for rule_date in list(rule_set):
            rule_data_w_tz = berlin_tz.localize(rule_date)
            eventDate = EventDate(event_id = result.id, start=rule_data_w_tz)
            result.dates.append(eventDate)
    else:
        eventDate = EventDate(event_id = result.id, start=start)
        result.dates.append(eventDate)

    if photo_res is not None:
        result.photo = upsert_image_with_res(result.photo, photo_res)

    return result

def get_event_hosts():
    # User permission, e.g. user is global admin
    if has_current_user_permission('event:create'):
        return OrgOrAdminUnit.query.all()

    # Admin unit member permissions (Holger, Artur)
    admin_units_the_user_is_member_of = admin_units_with_current_user_member_permission('event:create')

    # Admin org permissions (Mia)
    admin_units_via_orgs = admin_units_with_current_user_org_member_permission('event:create', 'event:create')

    # Org member permissions (Jason kann nur für Celtic Inn eintragen)
    organizations_the_user_is_member_of = organizations_with_current_user_org_member_permission('event:create')

    # Combine
    admin_units = admin_units_the_user_is_member_of
    admin_units.extend(admin_units_via_orgs)

    result = list()
    for admin_unit in admin_units:
        if not any(aao.id == admin_unit.org_or_adminunit.id for aao in result):
            result.append(admin_unit.org_or_adminunit)

        for admin_unit_org in admin_unit.organizations:
            if not any(admin_unit_org.organization is not None and aao.id == admin_unit_org.organization.org_or_adminunit.id for aao in result):
                result.append(admin_unit_org.organization.org_or_adminunit)

    for organization in organizations_the_user_is_member_of:
        if not any(aao.id == organization.org_or_adminunit.id for aao in result):
            result.append(organization.org_or_adminunit)

    return result

def admin_units_from_aaos(aaos):
    result = list()

    for aao in aaos:
        if aao.admin_unit is not None:
            result.append(aao.admin_unit)

    return result

# General permission checks

def has_admin_unit_member_permission(admin_unit_member, permission):
    for role in admin_unit_member.roles:
        if permission in role.get_permissions():
            return True
    return False

def has_admin_unit_org_permission(admin_unit_org, permission):
    for admin_unit_org_role in admin_unit_org.roles:
        if permission in admin_unit_org_role.get_permissions():
            return True

def has_org_member_permission(org_member, permission):
    for org_member_role in org_member.roles:
        if permission in org_member_role.get_permissions():
            return True
    return False

def has_any_admin_unit_permission_for_organization(organization_id, permission):
    admin_unit_orgs = AdminUnitOrg.query.filter_by(organization_id=organization_id).all()
    for admin_unit_org in admin_unit_orgs:
        if has_admin_unit_org_permission(admin_unit_org, permission):
            return True
    return False

def admin_units_with_permission_for_organization(organization_id, permission):
    result = list()

    admin_unit_orgs = AdminUnitOrg.query.filter_by(organization_id=organization_id).all()
    for admin_unit_org in admin_unit_orgs:
        if has_admin_unit_org_permission(admin_unit_org, permission):
            result.append(admin_unit_org.adminunit)

    return result

def admin_units_for_organization(organization_id):
    result = list()

    admin_unit_orgs = AdminUnitOrg.query.filter_by(organization_id=organization_id).all()
    for admin_unit_org in admin_unit_orgs:
        result.append(admin_unit_org.adminunit)

    return result

# Current User permission

# User permission, e.g. user is global admin
def has_current_user_permission(permission):
    user_perm = Permission(FsPermNeed(permission))
    if user_perm.can():
        return True

def has_current_user_member_permission_for_admin_unit(admin_unit_id, permission):
    admin_unit_member = AdminUnitMember.query.filter_by(admin_unit_id=admin_unit_id, user_id=current_user.id).first()
    if admin_unit_member is not None:
        if has_admin_unit_member_permission(admin_unit_member, permission):
            return True
    return False

def has_current_user_member_permission_for_any_admin_unit(permission):
    admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
    for admin_unit_member in admin_unit_members:
        if has_admin_unit_member_permission(admin_unit_member, permission):
            return True

    return False

def admin_units_with_current_user_member_permission(permission):
    result = list()
    admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
    for admin_unit_member in admin_unit_members:
        if has_admin_unit_member_permission(admin_unit_member, permission):
            result.append(admin_unit_member.adminunit)

    return result

def organizations_with_current_user_org_member_permission(permission):
    result = list()
    org_members = OrgMember.query.filter_by(user_id=current_user.id).all()
    for org_member in org_members:
        if has_org_member_permission(org_member, permission):
            result.append(org_member.organization)

    return result

def is_current_user_member_of_organization(organization_id, permission = None):
    org_member = OrgMember.query.filter_by(user_id=current_user.id, organization_id=organization_id).first()
    return (org_member is not None) and (permission is None or has_org_member_permission(org_member, permission))

def admin_units_with_current_user_org_member_permission(org_member_permission, admit_unit_org_permission):
    result = list()

    organizations = organizations_with_current_user_org_member_permission(org_member_permission)
    for organization in organizations:
        admin_units = admin_units_with_permission_for_organization(organization.id, admit_unit_org_permission)
        result.extend(admin_units)

    return result

def has_current_user_admin_unit_member_permission_for_organization(organization_id, admin_unit_member_permission):
    admin_units = admin_units_for_organization(organization_id)
    for admin_unit in admin_units:
        if has_current_user_member_permission_for_admin_unit(admin_unit.id, admin_unit_member_permission):
            return True
    return False

# Ist der Nutzer in einer Organisation mit entsprechender Permission und
# ist diese Organisation Teil einer Admin Unit mit der entsprechenden Permission?
def has_current_user_permissions_for_any_org_and_any_admin_unit(org_member_permission, admit_unit_org_permission):
    org_members = OrgMember.query.filter_by(user_id=current_user.id).all()
    for org_member in org_members:
        if has_org_member_permission(org_member, org_member_permission) and has_any_admin_unit_permission_for_organization(org_member.organization_id, admit_unit_org_permission):
            return True
    return False

def has_current_user_permissions_for_admin_unit_and_any_org(admin_unit_id, org_member_permission, admit_unit_org_permission):
    admin_unit_orgs = AdminUnitOrg.query.filter_by(admin_unit_id=admin_unit_id).all()
    for admin_unit_org in admin_unit_orgs:
        if has_admin_unit_org_permission(admin_unit_org, admit_unit_org_permission):
            org_member = OrgMember.query.filter_by(organization_id=admin_unit_org.organization_id, user_id=current_user.id).first()
            if org_member is not None and has_org_member_permission(org_member, org_member_permission):
                return True
    return False

# Type permissions

def can_list_admin_unit_members(admin_unit):
    if not current_user.is_authenticated:
        return False

    if has_current_user_permission('admin_unit.members:read'):
        return True

    if has_current_user_member_permission_for_admin_unit(admin_unit.id, 'admin_unit.members:read'):
        return True

    return False

def can_list_org_members(organization):
    if not current_user.is_authenticated:
        return False

    if has_current_user_permission('organization.members:read'):
        return True

    if has_current_user_admin_unit_member_permission_for_organization(organization.id, 'admin_unit.organizations.members:read'):
        return True

    if is_current_user_member_of_organization(organization.id):
        return True

    return False

def has_current_user_any_permission(user_permission, admin_unit_member_permission = None, org_member_permission = None, admit_unit_org_permission = None):
    if admin_unit_member_permission == None:
        admin_unit_member_permission = user_permission

    if org_member_permission == None:
        org_member_permission = user_permission

    if admit_unit_org_permission == None:
        admit_unit_org_permission = user_permission

    if not current_user.is_authenticated:
        return False

    # User permission, e.g. user is global admin
    if has_current_user_permission(user_permission):
        return True

    # Admin unit member permissions (Holger, Artur)
    if has_current_user_member_permission_for_any_admin_unit(admin_unit_member_permission):
        return True

    # Org member permissions (Mia)
    if has_current_user_permissions_for_any_org_and_any_admin_unit(org_member_permission, admit_unit_org_permission):
        return True

    # Org member permissions (Jason kann nur für Celtic Inn eintragen)
    if len(organizations_with_current_user_org_member_permission(org_member_permission)) > 0:
        return True

    return False

def can_create_event():
    return has_current_user_any_permission('event:create')

def can_verify_event(event):
    if not current_user.is_authenticated:
        return False

    # User permission, e.g. user is global admin
    if has_current_user_permission('event:verify'):
        return True

    # Admin unit member permissions (Holger, Artur)
    if has_current_user_member_permission_for_admin_unit(event.admin_unit_id, 'event:verify'):
        return True

    # Event has Admin Unit
    # Admin Unit has organization members with roles with permission 'event:verify'
    # This organization has members with roles with permission 'event:verify'
    # Der aktuelle nutzer muss unter diesen nutzern sein
    if has_current_user_permissions_for_admin_unit_and_any_org(event.admin_unit_id, 'event:verify', 'event:verify'):
        return True

    return False

def can_list_event_suggestion():
    return has_current_user_any_permission('event:verify')

def can_read_event_suggestion(suggestion):
    allowed_admin_units = admin_units_from_aaos(get_event_hosts())
    allowed_admin_unit_ids = [a.id for a in allowed_admin_units]

    return suggestion.admin_unit_id in allowed_admin_unit_ids

def get_event_suggestions_for_current_user():
    result = list()

    allowed_admin_units = admin_units_from_aaos(get_event_hosts())
    allowed_admin_unit_ids = [a.id for a in allowed_admin_units]

    suggestions = EventSuggestion.query.all()
    for suggestion in suggestions:
        if suggestion.admin_unit_id in allowed_admin_unit_ids:
            result.append(suggestion)

    return result

# Routes

@app.before_first_request
def create_user():
    # Event categories
    upsert_event_category('Art')
    upsert_event_category('Book')
    upsert_event_category('Movie')
    upsert_event_category('Family')
    upsert_event_category('Festival')
    upsert_event_category('Religious')
    upsert_event_category('Shopping')
    upsert_event_category('Comedy')
    upsert_event_category('Music')
    upsert_event_category('Dance')
    upsert_event_category('Nightlife')
    upsert_event_category('Theater')
    upsert_event_category('Dining')
    upsert_event_category('Conference')
    upsert_event_category('Meetup')
    upsert_event_category('Fitness')
    upsert_event_category('Sports')
    upsert_event_category('Other')
    db.session.commit()

    # Admin units
    goslar = upsert_admin_unit('Stadt Goslar')
    harzburg = upsert_admin_unit('Stadt Bad Harzburg')
    upsert_admin_unit('Stadt Clausthal')
    upsert_admin_unit('Gemeinde Walkenried')
    upsert_admin_unit('Stadt Bad Lauterberg')
    upsert_admin_unit('Stadt Harzgerode')
    upsert_admin_unit('Stadt Ilsenburg')
    upsert_admin_unit('Stadt Osterode')
    upsert_admin_unit('Stadt Quedlinburg')
    upsert_admin_unit('Stadt Wernigerode')
    upsert_admin_unit('Stadt Halberstadt')
    upsert_admin_unit('Gemeinde Wennigsen')
    upsert_admin_unit('Stadt Hildesheim')

    # Organizations
    admin_unit_org_event_verifier_role = upsert_admin_unit_org_role('event_verifier', ['event:verify', "event:create"])
    gmg = upsert_organization("GOSLAR marketing gmbh", "Markt 7", "38640", "Goslar", url='https://www.goslar.de/kontakt', logo_res="gmg.jpeg")
    gz = upsert_organization("Goslarsche Zeitung")
    celtic_inn = upsert_organization("Celtic Inn")
    kloster_woelteringerode = upsert_organization("Kloster Wöltingerode")
    miners_rock = upsert_organization("Miner's Rock", "Kuhlenkamp 36", "38640", "Goslar", legal_name="Miner's Rock UG (haftungsbeschränkt)", url="https://www.miners-rock.de/", logo_res="minersrock.jpeg")

    gmg_admin_unit_org = add_organization_to_admin_unit(gmg, goslar)
    add_role_to_admin_unit_org(gmg_admin_unit_org, admin_unit_org_event_verifier_role)

    gz_admin_unit_org = add_organization_to_admin_unit(gz, goslar)
    add_role_to_admin_unit_org(gz_admin_unit_org, admin_unit_org_event_verifier_role)

    add_organization_to_admin_unit(celtic_inn, goslar)
    add_organization_to_admin_unit(miners_rock, goslar)
    add_organization_to_admin_unit(upsert_organization("Aids-Hilfe Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Akademie St. Jakobushaus"), goslar)
    add_organization_to_admin_unit(upsert_organization("Aktiv für Hahndorf e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Aquantic Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Arbeitsgemeinschaft Hahndorfer Vereine und Verbände"), goslar)
    add_organization_to_admin_unit(upsert_organization("attac-Regionalgruppe Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Bildungshaus Zeppelin e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Brauhaus Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Buchhandlung Brumby"), goslar)
    add_organization_to_admin_unit(upsert_organization("Bühnenreif Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Bürgerstiftung Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Celtic-Inn Irish-Pub im Bahnhof"), goslar)
    add_organization_to_admin_unit(upsert_organization("Cineplex"), goslar)
    add_organization_to_admin_unit(upsert_organization("Der Zwinger zu Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("DERPART Reisebüro Goslar GmbH"), goslar)
    add_organization_to_admin_unit(upsert_organization("Deutscher Alpenverein Sektion Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("DGB - Frauen Goslar in der Region Südniedersachsen/Harz"), goslar)
    add_organization_to_admin_unit(upsert_organization("DGB-Kreisvorstand Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Die Butterhanne"), goslar)
    add_organization_to_admin_unit(upsert_organization("E-Bike Kasten"), goslar)
    add_organization_to_admin_unit(upsert_organization("Energie-Forschungszentrum der TU Clausthal - Geschäftsstelle Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("engesser marketing GmbH"), goslar)
    add_organization_to_admin_unit(upsert_organization("Ev. Kirchengemeinde St. Georg"), goslar)
    add_organization_to_admin_unit(upsert_organization("Förderkreis Goslarer Kleinkunsttage e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Frankenberger Kirche"), goslar)
    add_organization_to_admin_unit(upsert_organization("Frankenberger Winterabend"), goslar)
    add_organization_to_admin_unit(upsert_organization("Frauen-Arbeitsgemeinschaft im Landkreis Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("FreiwilligenAgentur Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Galerie Stoetzel-Tiedt"), goslar)
    add_organization_to_admin_unit(upsert_organization("Geschichtsverein GS e.V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Gesellschaft der Freunde und Förderer des Internationalen Musikfestes Goslar - Harz e.V."), goslar)
    add_organization_to_admin_unit(upsert_organization("GOSLAR marketing gmbh"), goslar)
    add_organization_to_admin_unit(upsert_organization("Goslarer Museum"), goslar)
    add_organization_to_admin_unit(upsert_organization("Goslarer Theater"), goslar)
    add_organization_to_admin_unit(upsert_organization("Goslarsche Höfe"), goslar)
    add_organization_to_admin_unit(upsert_organization("Goslarsche Zeitung"), goslar)
    add_organization_to_admin_unit(upsert_organization("Große Karnevalsgesellschaft Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Großes Heiliges Kreuz"), goslar)
    add_organization_to_admin_unit(upsert_organization("Hahndorfer Tennis Club 77 e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("HAHNENKLEE tourismus marketing gmbh"), goslar)
    add_organization_to_admin_unit(upsert_organization("HANSA Seniorenzentrum Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Harz Hochzeit"), goslar)
    add_organization_to_admin_unit(upsert_organization("Hotel Der Achtermann"), goslar)
    add_organization_to_admin_unit(upsert_organization("Internationale Goslarer Klaviertage "), goslar)
    add_organization_to_admin_unit(upsert_organization("Judo-Karate-Club Sportschule Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Kloster Wöltingerode Brennen &amp; Brauen GmbH"), goslar)
    add_organization_to_admin_unit(upsert_organization("Klosterhotel Wöltingerode"), goslar)
    add_organization_to_admin_unit(upsert_organization("Kontaktstelle Musik - Stadtmusikrat Goslar e.V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Kreisjugendpflege Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Kreismusikschule Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("KUBIK Event- und Musikklub"), goslar)
    add_organization_to_admin_unit(upsert_organization("Kulturgemeinschaft Vienenburg"), goslar)
    add_organization_to_admin_unit(upsert_organization("Kulturinitiative Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Lions Club Goslar Rammelsberg"), goslar)
    add_organization_to_admin_unit(upsert_organization("Marketing Club Harz"), goslar)
    add_organization_to_admin_unit(upsert_organization("Marktkirche Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Media Markt "), goslar)
    add_organization_to_admin_unit(upsert_organization("MGV Juventa von 1877 e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Mönchehaus Museum"), goslar)
    add_organization_to_admin_unit(upsert_organization("MTV Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Museumsverein Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("NABU Kreisgruppe Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Naturwissenschaftlicher Verein Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("PT Lounge Christian Brink"), goslar)
    add_organization_to_admin_unit(upsert_organization("Rampen für Goslar e.V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Residenz Schwiecheldthaus"), goslar)
    add_organization_to_admin_unit(upsert_organization("Romantik Hotel Alte Münze"), goslar)
    add_organization_to_admin_unit(upsert_organization("Schiefer"), goslar)
    add_organization_to_admin_unit(upsert_organization("Schwimmpark Aquantic"), goslar)
    add_organization_to_admin_unit(upsert_organization("Seniorenvertretung der Stadt Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Soup &amp; Soul Kitchen"), goslar)
    add_organization_to_admin_unit(upsert_organization("Stadtbibliothek Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Stadtjugendpflege Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Stadtteilverein Jerstedt e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Stiftung \"Maria in Horto\""), goslar)
    add_organization_to_admin_unit(upsert_organization("Verlag Goslarsche Zeitung"), goslar)
    add_organization_to_admin_unit(upsert_organization("Vienenburger Bürgerverein e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Volksfest Goslar e. V."), goslar)
    add_organization_to_admin_unit(upsert_organization("Weltkulturerbe Rammelsberg"), goslar)
    add_organization_to_admin_unit(upsert_organization("Zinnfigurenmuseum Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Zonta Club Goslar"), goslar)
    add_organization_to_admin_unit(upsert_organization("Zontaclub Goslar St. Barbar"), goslar)

    # Places
    upsert_place('Vienenburger See', 'In der Siedlung 4', '38690', 'Goslar', 51.958375, 10.559621)
    upsert_place('Feuerwehrhaus Hahndorf')
    upsert_place('Gemeindehaus St. Kilian Hahndorf')
    upsert_place('Grundschule Hahndorf')
    upsert_place('Mehrzweckhalle Hahndorf')
    upsert_place('Sportplatz Hahndorf')
    upsert_place('St. Kilian Hahndorf')
    upsert_place("Tourist-Information Goslar", 'Markt 7', '38644', 'Goslar', 51.906172, 10.429346, 'http://www.goslar.de/kontakt', "Zentral am Marktplatz gelegen, ist die Tourist-Information die erste Anlaufstelle für Goslar-Besucher. 14 motivierte und serviceorientierte Mitarbeiter sorgen dafür, dass sich der Gast rundherum wohl fühlt. Die ständige Qualitätsverbesserung und der flexible Umgang mit den Kundenwünschen sind Teil unserer Leitsätze.", 'touristinfo.jpeg')
    upsert_place("Nagelkopf am Rathaus Goslar", 'Marktkirchhof 3', '38640', 'Goslar', 51.9055939, 10.4263286)
    upsert_place("Kloster Wöltingerode", 'Wöltingerode 3', '38690', 'Goslar', 51.9591156, 10.5371815)
    upsert_place("Marktplatz Goslar", 'Markt 6', '38640', 'Goslar', 51.9063601, 10.4249433)
    upsert_place("Burg Vienenburg", 'Burgweg 2', '38690', 'Goslar', 51.9476558, 10.5617368)
    upsert_place("Kurhaus Bad Harzburg", 'Kurhausstraße 11', '38667', 'Bad Harzburg', 51.8758165, 10.5593392)
    upsert_place("Goslarsche Höfe", 'Okerstraße 32', '38640', 'Goslar', 51.911571, 10.4391331, 'https://www.goslarsche-hoefe.de/')
    upsert_place("Schlosserei im Rammelsberg", 'Bergtal 19', '38640', 'Goslar', 51.890527, 10.418880, 'http://www.rammelsberg.de/', 'Die "Schlosserei" ist erprobter Veranstaltungsort und bietet Platz für ca. 700 Besucher. Das Ambiente ist technisch gut ausgestattet und flexibel genug, für jeden Künstler individuell wandelbar zu sein. Dabei lebt nicht nur der Veranstaltungsraum, es wirkt der gesamte Komplex des Rammelsberges und macht den Besuch zu einem unvergeßlichen Erlebnis.', photo_res="schlosserei.jpeg")

    # Org or admins
    goslar_ooa = upsert_org_or_admin_unit_for_admin_unit(goslar)
    kloster_woelteringerode_ooa = upsert_org_or_admin_unit_for_organization(kloster_woelteringerode)
    gmg_ooa = upsert_org_or_admin_unit_for_organization(gmg)
    harzburg_ooa = upsert_org_or_admin_unit_for_admin_unit(harzburg)

    # Commit
    db.session.commit()

    # Users
    admin_role = user_datastore.find_or_create_role("admin")
    admin_role.add_permissions(["user:create", "event:verify", "event:create", "event_suggestion:read", "admin_unit.members:read", "organization.members:read"])

    admin_unit_admin_role = upsert_admin_unit_member_role('admin', ["admin_unit.members:read", "admin_unit.organizations.members:read"])
    admin_unit_event_verifier_role = upsert_admin_unit_member_role('event_verifier', ["event:verify", "event:create", "event_suggestion:read"])
    org_member_event_verifier_role = upsert_org_member_role('event_verifier', ["event:verify", "event:create", "event_suggestion:read"])
    org_member_event_creator_role = upsert_org_member_role('event_creator', ["event:create"])

    daniel = upsert_user("grams.daniel@gmail.com")
    user_datastore.add_role_to_user(daniel, admin_role)

    holger = upsert_user("holger@test.de")
    holger_goslar_member = add_user_to_admin_unit(holger, goslar)
    add_role_to_admin_unit_member(holger_goslar_member, admin_unit_admin_role)
    add_role_to_admin_unit_member(holger_goslar_member, admin_unit_event_verifier_role)

    artur = upsert_user("artur@test.de")
    artur_goslar_member = add_user_to_admin_unit(artur, goslar)
    add_role_to_admin_unit_member(artur_goslar_member, admin_unit_event_verifier_role)

    mia = upsert_user("mia@test.de")
    mia_gmg_member = add_user_to_organization(mia, gmg)
    add_role_to_org_member(mia_gmg_member, org_member_event_verifier_role)

    tom = upsert_user("tom@test.de")
    tom_gz_member = add_user_to_organization(tom, gz)
    add_role_to_org_member(tom_gz_member, org_member_event_verifier_role)

    jason = upsert_user("jason@test.de")
    jason_celtic_inn_member = add_user_to_organization(jason, celtic_inn)
    add_role_to_org_member(jason_celtic_inn_member, org_member_event_creator_role)

    grzno = upsert_user("grzno@test.de")
    grzno_miners_rock_member = add_user_to_organization(grzno, miners_rock)
    add_role_to_org_member(grzno_miners_rock_member, org_member_event_creator_role)

    # Events
    upsert_event("Vienenburger Seefest",
        goslar_ooa,
        "Vienenburger See",
        create_berlin_date(2020, 8, 14, 17, 0),
        'Vom 14. bis 16. August 2020 findet im ausgewiesenen Naherholungsgebiet am Fuße des Harzes, dem Goslarer Ortsteil Vienenburg, das Seefest unter dem Motto „Feuer & Wasser“ statt.',
        'https://www.goslar.de/kultur-freizeit/veranstaltungen/156-vienenburger-seefest?layout=*',
        True)

    upsert_event("Tausend Schritte durch die Altstadt",
        gmg_ooa,
        "Tourist-Information Goslar",
        create_berlin_date(2020, 1, 2, 10, 0),
        'Erleben Sie einen geführten Stadtrundgang durch den historischen Stadtkern. Lassen Sie sich von Fachwerkromantik und kaiserlichen Bauten inmitten der UNESCO-Welterbestätte verzaubern. ganzjährig (außer 01.01.) täglich 10:00 Uhr Treffpunkt: Tourist-Information am Marktplatz (Dauer ca. 2 Std.) Erwachsene 8,00 Euro Inhaber Gastkarte Goslar/Kurkarte Hahnenklee 7,00 Euro Schüler/Studenten 6,00 Euro',
        photo_res="tausend.jpeg",
        recurrence_rule="FREQ=DAILY;UNTIL=20201231T235959")

    upsert_event("Spaziergang am Nachmittag",
        gmg_ooa,
        "Tourist-Information Goslar",
        create_berlin_date(2020, 4, 1, 13, 30),
        'Begeben Sie sich auf einen geführten Rundgang durch die historische Altstadt. Entdecken Sie malerische Fachwerkgassen und imposante Bauwerke bei einem Streifzug durch das UNESCO-Weltkulturerbe. April – Oktober und 25.11. – 30.12. Montag – Samstag 13:30 Uhr Treffpunkt: Tourist-Information am Marktplatz (Dauer ca. 1,5 Std.) Erwachsene 7,00 Euro Inhaber Gastkarte Goslar/Kurkarte Hahnenklee 6,00 Euro Schüler/Studenten 5,00 Euro',
        photo_res="nachmittag.jpeg",
        recurrence_rule="""RRULE:FREQ=WEEKLY;UNTIL=20201031T235959;BYDAY=MO,TU,WE,TH,FR,SA""")

    upsert_event("Ein Blick hinter die Kulissen - Rathausbaustelle",
        goslar_ooa,
        "Nagelkopf am Rathaus Goslar",
        create_berlin_date(2020, 9, 3, 17, 0),
        'Allen interessierten Bürgern wird die Möglichkeit geboten, unter fachkundiger Führung des Goslarer Gebäudemanagement (GGM) einen Blick hinter die Kulissen durch das derzeit gesperrte historische Rathaus und die Baustelle Kulturmarktplatz zu werfen. Da bei beiden Führungen die Anzahl der Teilnehmer auf 16 Personen begrenzt ist, ist eine Anmeldung unbedingt notwendig sowie festes Schuhhwerk. Bitte melden Sie sich bei Interesse in der Tourist-Information (Tel. 05321-78060) an. Kinder unter 18 Jahren sind aus Sicherheitsgründen auf der Baustelle nicht zugelassen.')

    upsert_event("Wöltingerode unter Dampf",
        kloster_woelteringerode_ooa,
        "Kloster Wöltingerode",
        create_berlin_date(2020, 9, 5, 12, 0),
        'Mit einem ländlichen Programm rund um historische Trecker und Landmaschinen, köstliche Produkte aus Brennerei und Region, einem Kunsthandwerkermarkt und besonderen Führungen findet das Hoffest auf dem Klostergut statt.',
        'https://www.woelti-unter-dampf.de')

    upsert_event("Altstadtfest",
        gmg_ooa,
        "Marktplatz Goslar",
        create_berlin_date(2020, 9, 11, 15, 0),
        'Drei Tage lang dürfen sich die Besucher des Goslarer Altstadtfestes auf ein unterhaltsames und abwechslungsreiches Veranstaltungsprogramm freuen. Der Flohmarkt auf der Kaiserpfalzwiese lädt zum Stöbern vor historischer Kulisse ein.',
        'https://www.goslar.de/kultur-freizeit/veranstaltungen/altstadtfest')

    upsert_event("Adventsmarkt auf der Vienenburg",
        goslar_ooa,
        "Burg Vienenburg",
        create_berlin_date(2020, 12, 13, 12, 0),
        'Inmitten der mittelalterlichen Burg mit dem restaurierten Burgfried findet der „Advent auf der Burg“ statt. Der Adventsmarkt wird von gemeinnützigen und sozialen Vereinen sowie den Kirchen ausgerichtet.')

    upsert_event_suggestion("Der Blaue Vogel",
        "Freese-Baus Ballettschule",
        "Kurhaus Bad Harzburg",
        create_berlin_date(2020, 9, 12, 16, 0),
        'Die Freese-Baus Ballettschule zeigt 2020 ein wenig bekanntes französisches Märchen nach einer Erzählung Maurice Maeterlinck. Die Leiterin der Schule, Hanna-Sibylle Werner, hat die Grundidee übernommen, aber für ein Ballett überarbeitet, verändert und einstudiert. Das Märchen handelt von zwei Mädchen, die einen kleinen blauen Vogel lieb gewonnen haben, der über Nacht verschwunden ist. Mit Hilfe der Berylune und der Fee des Lichts machen sie sich auf den Weg, den Vogel wieder zu finden. Ihre Reise führt sie ins Reich der Erinnerung, des Glücks, der Phantasie und der Elemente. ( Die Einstudierung der Elemente: Luft, Wasser, Feuer übernahm der Choreograf Marco Barbieri, der auch zum Team der Ballettschule gehört ). Im Reich der Königin der Nacht finden sie ihren kleinen Vogel wieder, aber ob sie ihn mit nehmen dürfen, wird nicht verraten. Die Aufführungen werden durch farbenfrohe Kostüme ( Eigentum der Schule ) und Bühnenbilder ( Günter Werner ) ergänzt. Die Musik stammt von verschiedenen Komponisten. Die Tänzer*innen sind im Alter von 3 bis 40 Jahren, die Teilnahme ist für die älteren Schüler*innen freiwillig.',
        'https://veranstaltungen.meinestadt.de/bad-harzburg/event-detail/35486361/98831674',
        admin_unit = get_admin_unit('Stadt Bad Harzburg'))

    upsert_event_suggestion("Herbst-Flohmarkt",
        "Goslarsche Höfe - Integrationsbetrieb - gGmbH",
        "Goslarsche Höfe",
        create_berlin_date(2020, 10, 10, 10, 0),
        'Zum letzten Mal in dieser Saison gibt es einen Hof-Flohmarkt. Wir bieten zwar nicht den größten, aber vielleicht den gemütlichsten Flohmarkt in der Region. Frei von gewerblichen Anbietern, dafür mit Kaffee, Kuchen, Bier und Bratwurst, alles auf unserem schönen Hofgelände.',
        'https://www.goslarsche-hoefe.de/veranstaltungen/10/2175252/2020/10/10/herbst-flohmarkt.html')

    upsert_event('"MINER\'S ROCK" Schickt XVI - Lotte',
        miners_rock.org_or_adminunit,
        "Schlosserei im Rammelsberg",
        create_berlin_date(2020, 10, 31, 19, 0),
        'Auch im Jahr 2020 wagt sich das MINER’S ROCK wieder an eine Doppel-Schicht. LOTTE wird bei uns das Wochenende am Berg abrunden! Nach der bereits ausverkauften Schicht am 30. Oktober mit Subway to Sally, wird Lotte den Samstagabend zu einem Pop-Erlebnis machen.\nAb Anfang Februar ist sie in den Konzerthallen in Deutschland unterwegs und wird ihr neues Album „Glück“ vorstellen. Glück ist der langersehnte Nachfolger von LOTTEs Debütalbum „Querfeldein". Mit Songs wie der ersten Single „Schau mich nicht so an" oder dem Duett mit Max Giesinger „Auf das was da noch kommt“, durchmisst LOTTE dabei die Höhen und Tiefen des menschlichen Glücksstrebens. Und auch wenn jeder der zwölf Songs seine eigene Geschichte erzählt – sie alle eint die Suche nach der ganz persönlichen Bedeutung dieses großen Wortes. Glück ist kein Werk über einen abgeschlossenen Prozess, sondern ein beeindruckend ehrliches und facettenreiches Album über eine menschliche Suche. „Auf das was da noch kommt“ läuft derzeit in den Radiostationen auf und ab und macht einfach Spaß.\n\nWichtig zu wissen:\n\nEinlass: 19:00 Uhr\nBeginn des Musikprogramms: 20:00 Uhr\nTickets gibt es ab sofort im Shop des MINER‘S ROCK unter www.miners-rock.de und in den Geschäftsstellen der Goslarschen Zeitung.',
        'https://www.miners-rock.de/xvi-lotte',
        ticket_link='https://www.regiolights.de/tickets/product/schicht-xvi-lotte',
        photo_res="lotte.jpeg",
        category='Music')

    db.session.commit()

# Views
@app.route("/")
def home():
    admin_unit_members = AdminUnitMember.query.filter_by(user_id = current_user.id).all() if current_user.is_authenticated else None
    organization_members = OrgMember.query.filter_by(user_id = current_user.id).all() if current_user.is_authenticated else None
    return render_template('home.html',
        admin_unit_members=admin_unit_members,
        organization_members=organization_members)

@app.route("/admin_units")
def admin_units():
    return render_template('admin_units.html',
        admin_units=AdminUnit.query.order_by(asc(func.lower(AdminUnit.name))).all())

@app.route('/admin_unit/<int:admin_unit_id>')
def admin_unit(admin_unit_id):
    admin_unit = AdminUnit.query.filter_by(id = admin_unit_id).first()
    current_user_member = AdminUnitMember.query.with_parent(admin_unit).filter_by(user_id = current_user.id).first() if current_user.is_authenticated else None

    return render_template('admin_unit.html',
        admin_unit=admin_unit,
        current_user_member=current_user_member,
        can_list_admin_unit_members=can_list_admin_unit_members(admin_unit))

@app.route("/organizations")
def organizations():
    return render_template('organizations.html',
        organizations=Organization.query.order_by(asc(func.lower(Organization.name))).all())

@app.route('/organization/<int:organization_id>')
def organization(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    current_user_member = OrgMember.query.with_parent(organization).filter_by(user_id = current_user.id).first() if current_user.is_authenticated else None

    ooa = upsert_org_or_admin_unit_for_organization(organization)
    events = ooa.events

    return render_template('organization.html',
        organization=organization,
        current_user_member=current_user_member,
        can_list_members=can_list_org_members(organization),
        events=events)

@app.route('/image/<int:id>')
def image(id):
    image = Image.query.get_or_404(id)
    return app.response_class(image.data, mimetype=image.encoding_format)

@app.route("/profile")
@auth_required()
def profile():
    return render_template('profile.html')

@app.route("/places")
def places():
    places = Place.query.order_by(asc(func.lower(Place.name))).all()
    return render_template('place/list.html',
        places=places)

@app.route('/place/<int:place_id>')
def place(place_id):
    place = Place.query.filter_by(id = place_id).first()

    return render_template('place/read.html',
        place=place)

@app.route("/events")
def events():
    events = Event.query.all()
    return render_template('events.html',
        events=events,
        user_can_create_event=can_create_event(),
        user_can_list_event_suggestion=can_list_event_suggestion())

@app.route('/event/<int:event_id>', methods=('GET', 'POST'))
def event(event_id):
    event = Event.query.filter_by(id = event_id).first()
    user_can_verify_event = can_verify_event(event)

    if user_can_verify_event and request.method == 'POST':
        action = request.form['action']
        if action == 'verify':
            event.verified = True
        elif action == 'unverify':
            event.verified = False
        db.session.commit()

    return render_template('event.html', event=event, user_can_verify_event=user_can_verify_event)

@app.route("/eventdates")
def event_dates():
    dates = EventDate.query.filter(EventDate.start >= today).order_by(EventDate.start).all()
    return render_template('event_date/list.html',
        dates=dates)

@app.route('/eventdate/<int:id>', methods=('GET', 'POST'))
def event_date(id):
    event_date = EventDate.query.get_or_404(id)
    return render_template('event_date/read.html', event_date=event_date)

from forms.event import CreateEventForm
from forms.event_suggestion import CreateEventSuggestionForm

@app.route("/events/create", methods=('GET', 'POST'))
@auth_required()
def event_create():
    if not can_create_event():
        abort(401)

    form = CreateEventForm(category_id=upsert_event_category('Other').id)

    form.host_id.choices = sorted([(ooa.id, ooa.organization.name if ooa.organization is not None else ooa.admin_unit.name) for ooa in get_event_hosts()], key=lambda ooa: ooa[1])
    form.host_id.choices.insert(0, (0, ''))
    form.place_id.choices = [(p.id, p.name) for p in Place.query.order_by('name')]
    form.place_id.choices.insert(0, (0, ''))
    form.category_id.choices = sorted([(c.id, get_event_category_name(c)) for c in EventCategory.query.all()], key=lambda ooa: ooa[1])

    if form.validate_on_submit():
        event = Event()
        form.populate_obj(event)

        event.admin_unit = get_admin_unit('Stadt Goslar')

        eventDate = EventDate(event_id = event.id, start=form.start.data)
        event.dates.append(eventDate)

        if form.photo_file.data:
            fs = form.photo_file.data
            event.photo = upsert_image_with_data(event.photo, fs.read(), fs.content_type)

        db.session.commit()
        flash(gettext('Event successfully created'), 'success')
        return redirect(url_for('event', event_id=event.id))
    return render_template('event/create.html', form=form)

@app.route("/eventsuggestions")
@auth_required()
def eventsuggestions():
    if not can_list_event_suggestion():
        abort(401)

    return render_template('event_suggestion/list.html',
        suggestions=get_event_suggestions_for_current_user())

@app.route('/eventsuggestion/<int:event_suggestion_id>')
@auth_required()
def eventsuggestion(event_suggestion_id):
    suggestion = EventSuggestion.query.filter_by(id = event_suggestion_id).first()
    if not can_read_event_suggestion(suggestion):
        abort(401)

    return render_template('event_suggestion/read.html', suggestion=suggestion)

@app.route("/eventsuggestions/create", methods=('GET', 'POST'))
def event_suggestion_create():
    form = CreateEventSuggestionForm()
    if form.validate_on_submit():
        event = EventSuggestion()
        form.populate_obj(event)
        event.admin_unit = get_admin_unit('Stadt Goslar')
        eventDate = EventSuggestionDate(event_suggestion_id = event.id, start=form.start.data)
        event.dates.append(eventDate)
        db.session.commit()
        flash(gettext('Event suggestion successfully created'), 'success')
        return redirect(url_for('home'))
    return render_template('event_suggestion/create.html', form=form)

@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template('admin/admin.html')

@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    return render_template('admin/admin_units.html',
        admin_units=AdminUnit.query.all())

if __name__ == '__main__':
    app.run()