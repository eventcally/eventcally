import os
from base64 import b64decode
from flask import jsonify, Flask, render_template, request, url_for, redirect, abort, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import asc, func
from sqlalchemy import and_, or_, not_
from flask_security import Security, current_user, auth_required, roles_required, hash_password, SQLAlchemySessionUserDatastore
from flask_security.utils import FsPermNeed
from flask_babelex import Babel, gettext, lazy_gettext, format_datetime, to_user_timezone
from flask_principal import Permission
from flask_cors import CORS
from datetime import datetime
import pytz
import json
from urllib.parse import quote_plus
from dateutil.rrule import rrulestr, rruleset, rrule
from dateutil.relativedelta import relativedelta

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['LANGUAGES'] = ['en', 'de']
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

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

# cors
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# create db
db = SQLAlchemy(app)

from jsonld import DateTimeEncoder, get_sd_for_event_date
app.json_encoder = DateTimeEncoder

# Setup Flask-Security
# Define models
from models import EventRejectionReason, EventReviewStatus, EventPlace, EventOrganizer, EventCategory, Image, OrgOrAdminUnit, Actor, Place, Location, User, Role, AdminUnit, AdminUnitMember, AdminUnitMemberRole, OrgMember, OrgMemberRole, Organization, AdminUnitOrg, AdminUnitOrgRole, Event, EventDate
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)
from oauth import blueprint

app.register_blueprint(blueprint, url_prefix="/login")

berlin_tz = pytz.timezone('Europe/Berlin')
now = datetime.now(tz=berlin_tz)
today = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

def get_event_category_name(category):
    return lazy_gettext('Event_' + category.name)

app.jinja_env.filters['event_category_name'] = lambda u: get_event_category_name(u)

def get_localized_enum_name(enum):
    return lazy_gettext(enum.__class__.__name__ + '.' + enum.name)

app.jinja_env.filters['loc_enum'] = lambda u: get_localized_enum_name(u)

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
    gettext('Typical Age range')

def handleSqlError(e):
    message = str(e.__dict__['orig'])
    print(message)
    return message

def get_img_resource(res):
    with current_app.open_resource('static/img/' + res) as f:
        return f.read()

# Create a user to test with
def upsert_user(email, password="password"):
    result = user_datastore.find_user(email=email)
    if result is None:
        result = user_datastore.create_user(email=email, password=hash_password(password))
    return result

def upsert_admin_unit(unit_name, short_name = None):
    admin_unit = AdminUnit.query.filter_by(name = unit_name).first()
    if admin_unit is None:
        admin_unit = AdminUnit(name = unit_name)
        db.session.add(admin_unit)

    admin_unit.short_name = short_name
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

def upsert_organization(name, street = None, postalCode = None, city = None, latitude = 0, longitude = 0, legal_name = None, url=None, logo_res=None):
    result = Organization.query.filter_by(name = name).first()
    if result is None:
        result = Organization(name = name)
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

def upsert_location(street, postalCode, city, latitude = 0, longitude = 0, state = None):
    result = Location.query.filter_by(street = street, postalCode=postalCode, city=city, state=state).first()
    if result is None:
        result = Location(street = street, postalCode=postalCode, city=city, state=state)
        db.session.add(result)

    result.latitude = latitude
    result.longitude = longitude

    return result

def upsert_event_organizer(admin_unit_id, name):
    result = EventOrganizer.query.filter(and_(EventOrganizer.name == name, EventOrganizer.admin_unit_id == admin_unit_id)).first()
    if result is None:
        result = EventOrganizer(name = name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result

def upsert_event_place(admin_unit_id, organizer_id, name):
    result = EventPlace.query.filter(and_(EventPlace.name == name, EventPlace.admin_unit_id == admin_unit_id, EventPlace.organizer_id == organizer_id)).first()
    if result is None:
        result = EventPlace(name = name, admin_unit_id=admin_unit_id, organizer_id=organizer_id)
        result.location = Location()
        db.session.add(result)

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

def upsert_event_category(category_name):
    result = EventCategory.query.filter_by(name = category_name).first()
    if result is None:
        result = EventCategory(name = category_name)
        db.session.add(result)

    return result

def dates_from_recurrence_rule(start, recurrence_rule):
    result = list()

    adv_recurrence_rule = recurrence_rule.replace('T000000', 'T235959')
    start_wo_tz = start.replace(tzinfo=None)
    rule_set = rrulestr(adv_recurrence_rule, forceset=True, dtstart=start_wo_tz)

    start_date = start_wo_tz
    end_date = start_date + relativedelta(years=1)
    start_date_begin_of_day = datetime(start_date.year, start_date.month, start_date.day)
    end_date_end_of_day = datetime(end_date.year, end_date.month, end_date.day, hour=23, minute=59, second=59)

    for rule_date in rule_set.between(start_date_begin_of_day, end_date_end_of_day):
        rule_data_w_tz = berlin_tz.localize(rule_date)
        result.append(rule_data_w_tz)

    return result

def update_event_dates_with_recurrence_rule(event, start, end):
    event.start = start
    event.end = end

    if end:
        time_difference = relativedelta(end, start)

    dates_to_add = list()
    dates_to_remove = list(event.dates)

    if event.recurrence_rule:
        rr_dates = dates_from_recurrence_rule(start, event.recurrence_rule)
    else:
        rr_dates = [start]

    for rr_date in rr_dates:
        rr_date_start = date_add_time(rr_date, start.hour, start.minute, start.second, rr_date.tzinfo)

        if end:
            rr_date_end = rr_date_start + time_difference
        else:
            rr_date_end = None

        existing_date = next((date for date in event.dates if date.start == rr_date_start and date.end == rr_date_end), None)
        if existing_date:
            dates_to_remove.remove(existing_date)
        else:
            new_date = EventDate(event_id = event.id, start=rr_date_start, end=rr_date_end)
            dates_to_add.append(new_date)

    event.dates = [date for date in event.dates if date not in dates_to_remove]
    event.dates.extend(dates_to_add)

def get_admin_units_for_organizations():
    if has_current_user_permission('event:create'):
        return AdminUnit.query.all()

    return admin_units_the_current_user_is_member_of()

def get_admin_units_for_event():
    return AdminUnit.query.all()

def get_admin_units_for_manage():
    # Global admin
    if current_user.has_role('admin'):
        return AdminUnit.query.all()

    # Admin unit member permissions (Holger, Artur)
    admin_units_the_user_is_member_of = admin_units_with_current_user_member_permission('event:verify')

    # Admin org permissions (Marina)
    admin_units_via_orgs = admin_units_with_current_user_org_member_permission('event:verify', 'event:verify')

    admin_units = admin_units_the_user_is_member_of
    admin_units.extend(admin_units_via_orgs)

    return admin_units

def get_admin_unit_for_manage(admin_unit_id):
    admin_units = get_admin_units_for_manage()
    return next((au for au in admin_units if au.id == admin_unit_id), None)

def get_admin_unit_for_manage_or_404(admin_unit_id):
    admin_unit = get_admin_unit_for_manage(admin_unit_id)

    if not admin_unit:
        abort(404)

    return admin_unit

def get_event_hosts():
    if current_user.is_anonymous:
        return list()

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

def admin_units_the_current_user_is_member_of():
    result = list()
    admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
    for admin_unit_member in admin_unit_members:
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

def can_update_event(event):
    return can_create_event()

def can_delete_event(event):
    return can_update_event(event)

def can_create_place():
    return can_create_event()

def can_update_place(place):
    return can_create_place()

def can_create_organization():
    return can_create_event()

def can_update_organization(organization):
    return can_create_organization()

def can_update_organizer(organizer):
    return get_admin_unit_for_manage(organizer.admin_unit_id) is not None

def can_create_admin_unit():
    return current_user.is_authenticated

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

def assign_location_values(target, origin):
    if origin:
        target.street = origin.street
        target.postalCode = origin.postalCode
        target.city = origin.city
        target.state = origin.state
        target.country = origin.country
        target.latitude = origin.latitude
        target.longitude = origin.longitude

def get_pagination_urls(pagination, **kwargs):
    result = {}

    if pagination:
        if pagination.has_prev:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.prev_num
            result["prev_url"] = url_for(request.endpoint, **args)

        if pagination.has_next:
            args = request.args.copy()
            args.update(kwargs)
            args["page"] = pagination.next_num
            result["next_url"] = url_for(request.endpoint, **args)

    return result


# Routes

@app.before_first_request
def create_initial_data():
    pass

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext("Error in the %s field - %s") % (
                getattr(form, field).label.text,
                error
            ), 'danger')

# Views
@app.route("/")
def home():
    return render_template('home.html')

@app.route("/developer")
def developer():
    return render_template('developer/read.html')

@app.route("/admin_units")
def admin_units():
    return render_template('admin_unit/list.html',
        admin_units=AdminUnit.query.order_by(asc(func.lower(AdminUnit.name))).all())

@app.route('/admin_unit/<int:admin_unit_id>')
def admin_unit(admin_unit_id):
    admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
    current_user_member = AdminUnitMember.query.with_parent(admin_unit).filter_by(user_id = current_user.id).first() if current_user.is_authenticated else None

    return render_template('admin_unit/read.html',
        admin_unit=admin_unit,
        current_user_member=current_user_member,
        can_list_admin_unit_members=can_list_admin_unit_members(admin_unit),
        can_update_admin_unit=has_current_user_permission('admin_unit:update'))

def update_admin_unit_with_form(admin_unit, form):
    form.populate_obj(admin_unit)

    if form.logo_file.data:
        fs = form.logo_file.data
        admin_unit.logo = upsert_image_with_data(admin_unit.logo, fs.read(), fs.content_type)

# @app.route('/admin_unit/<int:admin_unit_id>/update', methods=('GET', 'POST'))
# def admin_unit_update(admin_unit_id):
#     if not has_current_user_permission('admin_unit:update'):
#         abort(401)

#     admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
#     form = UpdateAdminUnitForm(obj=admin_unit)

#     if form.validate_on_submit():
#         if not admin_unit.location:
#             admin_unit.location = Location()
#         update_admin_unit_with_form(admin_unit, form)

#         try:
#             db.session.commit()
#             flash(gettext('Admin unit successfully updated'), 'success')
#             return redirect(url_for('admin_unit', admin_unit_id=admin_unit.id))
#         except SQLAlchemyError as e:
#             db.session.rollback()
#             flash(handleSqlError(e), 'danger')

#     return render_template('admin_unit/update.html',
#         form=form,
#         admin_unit=admin_unit)

@app.route("/organizations")
def organizations():
    return render_template('organization/list.html',
        organizations=Organization.query.order_by(asc(func.lower(Organization.name))).all(),
        can_create_organization=can_create_organization())

@app.route('/organization/<int:organization_id>')
def organization(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    current_user_member = OrgMember.query.with_parent(organization).filter_by(user_id = current_user.id).first() if current_user.is_authenticated else None

    ooa = upsert_org_or_admin_unit_for_organization(organization)
    events = ooa.events

    return render_template('organization/read.html',
        organization=organization,
        current_user_member=current_user_member,
        can_list_members=can_list_org_members(organization),
        events=events,
        can_update_organization=can_update_organization(organization))

def update_organization_with_form(organization, form):
    form.populate_obj(organization)

    if form.logo_file.data:
        fs = form.logo_file.data
        organization.logo = upsert_image_with_data(organization.logo, fs.read(), fs.content_type)

@app.route("/organization/create", methods=('GET', 'POST'))
def organization_create():
    if not can_create_organization():
        abort(401)

    form = CreateOrganizationForm()
    form.admin_unit_id.choices = sorted([(admin_unit.id, admin_unit.name) for admin_unit in get_admin_units_for_organizations()], key=lambda admin_unit: admin_unit[1])

    if form.validate_on_submit():
        organization = Organization()
        organization.location = Location()
        update_organization_with_form(organization, form)

        admin_unit = AdminUnit.query.get_or_404(form.admin_unit_id.data)
        add_organization_to_admin_unit(organization, admin_unit)

        try:
            db.session.add(organization)
            upsert_org_or_admin_unit_for_organization(organization)
            db.session.commit()
            flash(gettext('Organization successfully created'), 'success')
            return redirect(url_for('organization', organization_id=organization.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('organization/create.html', form=form)

@app.route('/organization/<int:organization_id>/update', methods=('GET', 'POST'))
def organization_update(organization_id):
    organization = Organization.query.get_or_404(organization_id)

    if not can_update_organization(organization):
        abort(401)

    form = UpdateOrganizationForm(obj=organization)

    if form.validate_on_submit():
        update_organization_with_form(organization, form)

        try:
            db.session.commit()
            flash(gettext('Organization successfully updated'), 'success')
            return redirect(url_for('organization', organization_id=organization.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('organization/update.html',
        form=form,
        organization=organization)

def update_admin_unit_with_form(admin_unit, form):
    form.populate_obj(admin_unit)

    if form.logo_file.data:
        fs = form.logo_file.data
        admin_unit.logo = upsert_image_with_data(admin_unit.logo, fs.read(), fs.content_type)

@app.route("/admin_unit/create", methods=('GET', 'POST'))
@auth_required()
def admin_unit_create():
    if not can_create_admin_unit():
        abort(401)

    form = CreateAdminUnitForm()

    if form.validate_on_submit():
        admin_unit = AdminUnit()
        admin_unit.location = Location()
        update_admin_unit_with_form(admin_unit, form)

        try:
            db.session.add(admin_unit)
            upsert_org_or_admin_unit_for_admin_unit(admin_unit)

            # Aktuellen Nutzer als Admin hinzufügen
            member = add_user_to_admin_unit(current_user, admin_unit)
            admin_unit_admin_role = upsert_admin_unit_member_role('admin', ["admin_unit.members:read", "admin_unit.organizations.members:read"])
            admin_unit_event_verifier_role = upsert_admin_unit_member_role('event_verifier', ["event:verify", "event:create", "event_suggestion:read"])
            add_role_to_admin_unit_member(member, admin_unit_admin_role)
            add_role_to_admin_unit_member(member, admin_unit_event_verifier_role)
            db.session.commit()

            # Organizer anlegen
            organizer = EventOrganizer()
            organizer.admin_unit_id = admin_unit.id
            organizer.name = admin_unit.name
            organizer.url = admin_unit.url
            organizer.email = admin_unit.email
            organizer.phone = admin_unit.phone
            organizer.fax = admin_unit.fax
            organizer.location = Location()
            assign_location_values(organizer.location, admin_unit.location)
            if admin_unit.logo:
                organizer.logo = upsert_image_with_data(organizer.logo, admin_unit.logo.data, admin_unit.logo.encoding_format)
            db.session.add(organizer)
            db.session.commit()

            flash(gettext('Admin unit successfully created'), 'success')
            return redirect(url_for('manage_admin_unit', id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('admin_unit/create.html', form=form)

@app.route('/admin_unit/<int:admin_unit_id>/update', methods=('GET', 'POST'))
@auth_required()
def admin_unit_update(admin_unit_id):
    admin_unit = get_admin_unit_for_manage_or_404(admin_unit_id)

    form = UpdateAdminUnitForm(obj=admin_unit)

    if form.validate_on_submit():
        update_admin_unit_with_form(admin_unit, form)

        try:
            db.session.commit()
            flash(gettext('AdminUnit successfully updated'), 'success')
            return redirect(url_for('manage_admin_unit', id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('admin_unit/update.html',
        form=form,
        admin_unit=admin_unit)

@app.route('/image/<int:id>')
def image(id):
    image = Image.query.get_or_404(id)
    return app.response_class(image.data, mimetype=image.encoding_format)

@app.route("/profile")
@auth_required()
def profile():
    admin_unit_members = AdminUnitMember.query.filter_by(user_id = current_user.id).all() if current_user.is_authenticated else None
    organization_members = OrgMember.query.filter_by(user_id = current_user.id).all() if current_user.is_authenticated else None
    return render_template('profile.html',
        admin_unit_members=admin_unit_members,
        organization_members=organization_members)

@app.route("/places")
def places():
    places = Place.query.order_by(asc(func.lower(Place.name))).all()
    return render_template('place/list.html',
        places=places,
        can_create_place=can_create_place())

@app.route('/place/<int:place_id>')
def place(place_id):
    place = Place.query.get_or_404(place_id)

    return render_template('place/read.html',
        place=place,
        can_update_place=can_update_place(place))

def update_place_with_form(place, form):
    form.populate_obj(place)

    if form.photo_file.data:
        fs = form.photo_file.data
        place.photo = upsert_image_with_data(place.photo, fs.read(), fs.content_type)

@app.route('/place/<int:place_id>/update', methods=('GET', 'POST'))
def place_update(place_id):
    place = Place.query.get_or_404(place_id)

    if not can_update_place(place):
        abort(401)

    form = UpdatePlaceForm(obj=place)

    if form.validate_on_submit():
        update_place_with_form(place, form)

        try:
            db.session.commit()
            flash(gettext('Place successfully updated'), 'success')
            return redirect(url_for('place', place_id=place.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('place/update.html',
        form=form,
        place=place)

@app.route("/place/create", methods=('GET', 'POST'))
def place_create():
    if not can_create_place():
        abort(401)

    form = CreatePlaceForm()
    if form.validate_on_submit():
        place = Place()
        place.location = Location()
        update_place_with_form(place, form)

        try:
            db.session.add(place)
            db.session.commit()
            flash(gettext('Place successfully created'), 'success')
            return redirect(url_for('place', place_id=place.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('place/create.html', form=form)

@app.route("/events")
def events():
    events = Event.query.order_by(Event.start).all()
    return render_template('event/list.html',
        events=events)

@app.route('/event/<int:event_id>')
def event(event_id):
    event = Event.query.get_or_404(event_id)
    dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()
    user_can_verify_event = can_verify_event(event)
    user_can_update_event = can_update_event(event)

    if not event.verified and not user_can_verify_event and not user_can_update_event:
        abort(401)

    return render_template('event/read.html',
        event=event,
        dates=dates,
        user_can_verify_event=user_can_verify_event,
        can_update_event=user_can_update_event)

@app.route('/event/<int:event_id>/review', methods=('GET', 'POST'))
def event_review(event_id):
    event = Event.query.get_or_404(event_id)
    dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()
    user_can_verify_event = can_verify_event(event)

    if not user_can_verify_event:
        abort(401)

    form = ReviewEventForm(obj=event)

    if form.validate_on_submit():
        form.populate_obj(event)

        if event.review_status != EventReviewStatus.rejected:
            event.rejection_resaon = None

        if event.rejection_resaon == 0:
            event.rejection_resaon = None

        try:
            db.session.commit()
            flash(gettext('Event successfully updated'), 'success')
            return redirect(url_for('manage_admin_unit_event_reviews', id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/review.html',
        form=form,
        dates=dates,
        event=event)

@app.route("/eventdates")
def event_dates():
    dates = EventDate.query.filter(EventDate.start >= today).order_by(EventDate.start).all()
    return render_template('event_date/list.html',
        dates=dates)

@app.route('/eventdate/<int:id>')
def event_date(id):
    event_date = EventDate.query.get_or_404(id)
    structured_data = json.dumps(get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder)
    return render_template('event_date/read.html',
        event_date=event_date,
        structured_data=structured_data)

@app.route("/api/events")
def api_events():
    dates = EventDate.query.join(Event).filter(EventDate.start >= today).filter(Event.verified).order_by(EventDate.start).all()
    structured_events = list()
    for event_date in dates:
        structured_event = get_sd_for_event_date(event_date)
        structured_event.pop('@context', None)
        structured_events.append(structured_event)

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Project"
    result["name"] = "Prototyp"
    result['event'] = structured_events
    return jsonify(result)

@app.route("/api/organizer/<int:id>/event_places")
def api_event_places(id):
    places = get_event_places(id)
    result = list()

    for place in places:
        item = {}
        item["id"] = place.id
        item["name"] = place.name
        result.append(item)

    return jsonify(result)

from forms.event import CreateEventForm, UpdateEventForm, DeleteEventForm, EventContactForm, ReviewEventForm
from forms.place import CreatePlaceForm, UpdatePlaceForm
from forms.organization import CreateOrganizationForm, UpdateOrganizationForm
from forms.organizer import CreateOrganizerForm, UpdateOrganizerForm, DeleteOrganizerForm
from forms.admin_unit import CreateAdminUnitForm, UpdateAdminUnitForm

def update_event_with_form(event, form):
    form.populate_obj(event)

    if event.host_id == 0:
        event.host_id = None

    if event.place_id == 0:
        event.place_id = None

    update_event_dates_with_recurrence_rule(event, form.start.data, form.end.data)

    if form.photo_file.data:
        fs = form.photo_file.data
        event.photo = upsert_image_with_data(event.photo, fs.read(), fs.content_type)

def get_event_places(organizer_id):
    organizer = EventOrganizer.query.get(organizer_id)
    return EventPlace.query.filter(or_(EventPlace.organizer_id == organizer_id, and_(EventPlace.public, EventPlace.admin_unit_id==organizer.admin_unit_id))).order_by(func.lower(EventPlace.name)).all()

def prepare_event_form(form):
    form.organizer_id.choices = [(o.id, o.name) for o in EventOrganizer.query.filter(EventOrganizer.admin_unit_id == form.admin_unit_id.data).order_by(func.lower(EventOrganizer.name))]
    form.category_id.choices = sorted([(c.id, get_event_category_name(c)) for c in EventCategory.query.all()], key=lambda ooa: ooa[1])
    form.admin_unit_id.choices = sorted([(admin_unit.id, admin_unit.name) for admin_unit in get_admin_units_for_event()], key=lambda admin_unit: admin_unit[1])

    if form.organizer_id.data:
        places = get_event_places(form.organizer_id.data)
        form.event_place_id.choices = [(p.id, p.name) for p in places]
    else:
        form.event_place_id.choices = list()

    form.organizer_id.choices.insert(0, (0, ''))
    form.event_place_id.choices.insert(0, (0, ''))

def event_create_base(admin_unit, organizer_id=0):
    form = CreateEventForm(admin_unit_id=admin_unit.id, organizer_id=organizer_id, category_id=upsert_event_category('Other').id)
    prepare_event_form(form)

    current_user_can_create_event = can_create_event()

    if not current_user_can_create_event:
        form.contact.min_entries = 1
        if len(form.contact.entries) == 0:
            form.contact.append_entry()

    if form.validate_on_submit():
        event = Event()
        update_event_with_form(event, form)

        if form.event_place_choice.data == 2:
            event.event_place.organizer_id = event.organizer_id
            event.event_place.admin_unit_id = event.admin_unit_id

        current_user_can_verify_event = can_verify_event(event)
        if current_user_can_verify_event:
            event.review_status = EventReviewStatus.verified
        else:
            event.review_status = EventReviewStatus.inbox

        try:
            db.session.add(event)
            db.session.commit()

            if current_user_can_verify_event:
                flash(gettext('Event successfully created'), 'success')
                return redirect(url_for('event', event_id=event.id))
            else:
                flash(gettext('Thank you so much! The event is being verified.'), 'success')
                return redirect(url_for('event_review_status', event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)
    return render_template('event/create.html', form=form)

@app.route('/event/<int:event_id>/review_status')
def event_review_status(event_id):
    event = Event.query.get_or_404(event_id)

    return render_template('event/review_status.html',
        event=event)

@app.route("/<string:au_short_name>/events/create", methods=('GET', 'POST'))
def event_create_for_admin_unit(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()
    return event_create_base(admin_unit)

@app.route("/admin_unit/<int:id>/events/create", methods=('GET', 'POST'))
def event_create_for_admin_unit_id(id):
    admin_unit = AdminUnit.query.get_or_404(id)
    organizer_id = request.args.get('organizer_id') if 'organizer_id' in request.args else 0
    return event_create_base(admin_unit, organizer_id)

@app.route('/event/<int:event_id>/update', methods=('GET', 'POST'))
def event_update(event_id):
    event = Event.query.get_or_404(event_id)

    if not can_update_event(event):
        abort(401)

    form = UpdateEventForm(obj=event,start=event.start,end=event.end)
    prepare_event_form(form)

    if form.validate_on_submit():
        update_event_with_form(event, form)

        try:
            db.session.commit()
            flash(gettext('Event successfully updated'), 'success')
            return redirect(url_for('event', event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/update.html',
        form=form,
        event=event)

@app.route('/event/<int:event_id>/delete', methods=('GET', 'POST'))
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)

    if not can_delete_event(event):
        abort(401)

    form = DeleteEventForm()

    if form.validate_on_submit():
        if form.name.data != event.name:
            flash(gettext('Entered name does not match event name'), 'danger')
        else:
            try:
                db.session.delete(event)
                db.session.commit()
                flash(gettext('Event successfully deleted'), 'success')
                return redirect(url_for('manage_organizer_events', organizer_id=event.organizer_id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/delete.html',
        form=form,
        event=event)

@app.route("/events/rrule", methods=['POST'])
def event_rrule():
    year = request.json['year']
    month = request.json['month']
    day = request.json['day']
    rrule_str = request.json['rrule']
    output_format = request.json['format']
    start = int(request.json['start'])
    batch_size = 10
    start_date = datetime(year, month, day)

    from utils import calculate_occurrences
    result = calculate_occurrences(start_date, '"%d.%m.%Y"', rrule_str, start, batch_size)
    return jsonify(result)

@app.route("/admin")
@roles_required("admin")
def admin():
    return render_template('admin/admin.html')

@app.route("/admin/admin_units")
@roles_required("admin")
def admin_admin_units():
    return render_template('admin/admin_units.html',
        admin_units=AdminUnit.query.all())

@app.route("/manage")
def manage():
    admin_units = get_admin_units_for_manage()

    # if len(admin_units) == 1:
    #     return redirect(url_for('manage_admin_unit', id=admin_units[0].id))

    return render_template('manage/admin_units.html',
        admin_units=admin_units)

@app.route('/manage/admin_unit/<int:id>')
def manage_admin_unit(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    return redirect(url_for('manage_admin_unit_event_reviews', id=admin_unit.id))

    return render_template('manage/admin_unit.html',
        admin_unit=admin_unit)

@app.route('/manage/admin_unit/<int:id>/organizers')
def manage_admin_unit_organizers(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).paginate()

    return render_template('manage/organizers.html',
        admin_unit=admin_unit,
        organizers=organizers.items,
        pagination=get_pagination_urls(organizers, id=id))

@app.route('/manage/admin_unit/<int:id>/event_places')
def manage_admin_unit_event_places(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizer = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).first()

    if organizer:
        return redirect(url_for('manage_organizer_event_places', organizer_id=organizer.id))

    flash('Please create an organizer before you create a place', 'danger')
    return redirect(url_for('manage_admin_unit_organizers', id=id))

from forms.event_place import FindEventPlaceForm

@app.route('/manage/event_places')
def manage_organizer_event_places():
    organizer = EventOrganizer.query.get_or_404(request.args.get('organizer_id'))
    admin_unit = get_admin_unit_for_manage_or_404(organizer.admin_unit_id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).all()

    form = FindEventPlaceForm(**request.args)
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]

    places = EventPlace.query.filter(EventPlace.organizer_id == organizer.id).order_by(func.lower(EventPlace.name)).paginate()
    return render_template('manage/places.html',
        admin_unit=admin_unit,
        organizer=organizer,
        form=form,
        places=places.items,
        pagination=get_pagination_urls(places))

@app.route('/manage/admin_unit/<int:id>/events')
def manage_admin_unit_events(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    organizer = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).first()

    if organizer:
        return redirect(url_for('manage_organizer_events', organizer_id=organizer.id))

    flash('Please create an organizer before you create an event', 'danger')
    return redirect(url_for('manage_admin_unit_organizers', id=id))

from forms.event import FindEventForm

@app.route('/manage/events')
def manage_organizer_events():
    organizer = EventOrganizer.query.get_or_404(request.args.get('organizer_id'))
    admin_unit = get_admin_unit_for_manage_or_404(organizer.admin_unit_id)
    organizers = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name)).all()

    keyword = request.args.get('keyword') if 'keyword' in request.args else ""

    form = FindEventForm(**request.args)
    form.organizer_id.choices = [(o.id, o.name) for o in organizers]

    if keyword:
        like_keyword = '%' + keyword + '%'
        event_filter = and_(Event.organizer_id == organizer.id, Event.review_status != EventReviewStatus.inbox, Event.name.ilike(like_keyword))
    else:
        event_filter = and_(Event.organizer_id == organizer.id, Event.review_status != EventReviewStatus.inbox)

    events = Event.query.filter(event_filter).order_by(Event.start).paginate()
    return render_template('manage/events.html',
        admin_unit=admin_unit,
        organizer=organizer,
        form=form,
        events=events.items,
        pagination=get_pagination_urls(events))

@app.route('/manage/admin_unit/<int:id>/reviews')
def manage_admin_unit_event_reviews(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_current_user_any_permission('event:verify'):
        events = list()
        events_paginate = None
    else:
        events_paginate = Event.query.filter(and_(Event.admin_unit_id == admin_unit.id, Event.review_status == EventReviewStatus.inbox)).order_by(Event.start).paginate()
        events = events_paginate.items

    return render_template('manage/reviews.html',
        admin_unit=admin_unit,
        events=events,
        pagination = get_pagination_urls(events_paginate, id=id))

from forms.event import FindEventForm

@app.route('/organizer/<int:id>')
def organizer(id):
    organizer = EventOrganizer.query.get_or_404(id)

    return render_template('organizer/read.html',
        organizer=organizer,
        can_update_organizer=can_update_organizer(organizer))

def update_organizer_with_form(organizer, form):
    form.populate_obj(organizer)

    if form.logo_file.data:
        fs = form.logo_file.data
        organizer.logo = upsert_image_with_data(organizer.logo, fs.read(), fs.content_type)

@app.route('/manage/admin_unit/<int:id>/organizers/create', methods=('GET', 'POST'))
def manage_admin_unit_organizer_create(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    form = CreateOrganizerForm()

    if form.validate_on_submit():
        organizer = EventOrganizer()
        organizer.admin_unit_id = admin_unit.id
        organizer.location = Location()
        update_organizer_with_form(organizer, form)

        try:
            db.session.add(organizer)
            db.session.commit()
            flash(gettext('Organizer successfully created'), 'success')
            #return redirect(url_for('organizer', id=organizer.id))
            return redirect(url_for('manage_admin_unit_organizers', id=organizer.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('organizer/create.html', form=form)

@app.route('/organizer/<int:id>/update', methods=('GET', 'POST'))
def organizer_update(id):
    organizer = EventOrganizer.query.get_or_404(id)

    if not can_update_organizer(organizer):
        abort(401)

    form = UpdateOrganizerForm(obj=organizer)

    if form.validate_on_submit():
        update_organizer_with_form(organizer, form)

        try:
            db.session.commit()
            flash(gettext('Organizer successfully updated'), 'success')
            #return redirect(url_for('organizer', id=organizer.id))
            return redirect(url_for('manage_admin_unit_organizers', id=organizer.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('organizer/update.html',
        form=form,
        organizer=organizer)

@app.route('/organizer/<int:id>/delete', methods=('GET', 'POST'))
def organizer_delete(id):
    organizer = EventOrganizer.query.get_or_404(id)

    if not can_update_organizer(organizer):
        abort(401)

    form = DeleteOrganizerForm()

    if form.validate_on_submit():
        if form.name.data != organizer.name:
            flash(gettext('Entered name does not match organizer name'), 'danger')
        else:
            try:
                db.session.delete(organizer)
                db.session.commit()
                flash(gettext('Organizer successfully deleted'), 'success')
                return redirect(url_for('manage_admin_unit_organizers', id=organizer.admin_unit_id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('organizer/delete.html',
        form=form,
        organizer=organizer)

def update_event_place_with_form(place, form):
    form.populate_obj(place)

    if form.photo_file.data:
        fs = form.photo_file.data
        place.photo = upsert_image_with_data(place.photo, fs.read(), fs.content_type)

from forms.event_place import UpdateEventPlaceForm, CreateEventPlaceForm

@app.route('/event_place/<int:id>/update', methods=('GET', 'POST'))
def event_place_update(id):
    place = EventPlace.query.get_or_404(id)

    if not can_update_organizer(place.organizer):
        abort(401)

    form = UpdateEventPlaceForm(obj=place)

    if form.validate_on_submit():
        update_event_place_with_form(place, form)

        try:
            db.session.commit()
            flash(gettext('Place successfully updated'), 'success')
            return redirect(url_for('manage_organizer_event_places', organizer_id=place.organizer.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('event_place/update.html',
        form=form,
        place=place)

@app.route('/manage/organizer/<int:id>/places/create', methods=('GET', 'POST'))
def manage_organizer_places_create(id):
    organizer = EventOrganizer.query.get_or_404(id)

    if not can_update_organizer(organizer):
        abort(401)

    form = CreateEventPlaceForm()

    if form.validate_on_submit():
        place = EventPlace()
        place.organizer_id = organizer.id
        place.admin_unit_id = organizer.admin_unit_id
        place.location = Location()
        update_event_place_with_form(place, form)

        try:
            db.session.add(place)
            db.session.commit()
            flash(gettext('Place successfully created'), 'success')
            return redirect(url_for('manage_organizer_event_places', organizer_id=organizer.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('event_place/create.html', form=form)

def date_add_time(date, hour=0, minute=0, second=0, tzinfo=None):
    return datetime(date.year, date.month, date.day, hour=hour, minute=minute, second=second, tzinfo=tzinfo)

def date_set_end_of_day(date):
    return date_add_time(date, hour=23, minute=59, second=59)

def form_input_to_date(date_str, hour=0, minute=0, second=0):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date_time = date_add_time(date, hour=hour, minute=minute, second=second)
    return berlin_tz.localize(date_time)

def form_input_from_date(date):
    return date.strftime("%Y-%m-%d")

@app.route("/<string:au_short_name>/widget/eventdates")
def widget_event_dates(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()

    date_from = today
    date_to = date_set_end_of_day(today + relativedelta(months=12))
    date_from_str = form_input_from_date(date_from)
    date_to_str = form_input_from_date(date_to)
    keyword = ''

    if 'date_from' in request.args:
        date_from_str = request.args['date_from']
        date_from = form_input_to_date(date_from_str)

    if 'date_to' in request.args:
        date_to_str = request.args['date_to']
        date_to = form_input_to_date(date_to_str)

    if 'keyword' in request.args:
        keyword = request.args['keyword']

    date_filter = and_(EventDate.start >= date_from, EventDate.start < date_to)

    if keyword:
        like_keyword = '%' + keyword + '%'
        event_filter = and_(Event.admin_unit_id == admin_unit.id, Event.verified, or_(Event.name.ilike(like_keyword), Event.description.ilike(like_keyword), Event.tags.ilike(like_keyword)))
    else:
        event_filter = and_(Event.admin_unit_id == admin_unit.id, Event.verified)

    dates = EventDate.query.join(Event).filter(date_filter).filter(event_filter).order_by(EventDate.start).paginate()

    return render_template('widget/event_date/list.html',
        date_from_str=date_from_str,
        date_to_str=date_to_str,
        keyword=keyword,
        dates=dates.items,
        pagination=get_pagination_urls(dates, au_short_name=au_short_name))

@app.route('/widget/eventdate/<int:id>')
def widget_event_date(id):
    event_date = EventDate.query.get_or_404(id)
    structured_data = json.dumps(get_sd_for_event_date(event_date), indent=2, cls=DateTimeEncoder)
    return render_template('widget/event_date/read.html',
        event_date=event_date,
        structured_data=structured_data)

if __name__ == '__main__':
    app.run()