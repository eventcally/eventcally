import os
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_security import Security, current_user, auth_required, roles_required, hash_password, SQLAlchemySessionUserDatastore
from flask_security.utils import FsPermNeed
from flask_babelex import Babel, gettext, lazy_gettext, format_datetime
from flask_principal import Permission
from datetime import datetime
import pytz

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

# create db
db = SQLAlchemy(app)

# Setup Flask-Security
# Define models
from models import User, Role, AdminUnit, AdminUnitMember, AdminUnitMemberRole, OrgMember, OrgMemberRole, Organization, AdminUnitOrg, AdminUnitOrgRole, Event, EventDate
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

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
    return admin_unit

def get_admin_unit(unit_name):
    return AdminUnit.query.filter_by(name = unit_name).first()

def upsert_org_member_role(role_name, permissions):
    result = OrgMemberRole.query.filter_by(name = role_name).first()
    if result is None:
        result = OrgMemberRole(name = role_name)
        result.remove_permissions(result.get_permissions())
        result.add_permissions(permissions)
        db.session.add(result)
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

def upsert_organization(org_name):
    result = Organization.query.filter_by(name = org_name).first()
    if result is None:
        result = Organization(name = org_name)
        db.session.add(result)
    return result

def create_berlin_date(year, month, day, hour, minute = 0):
    return pytz.timezone('Europe/Berlin').localize(datetime(year, month, day, hour=hour, minute=minute))

def upsert_event(event_name, host, location, start, description, link = None, verified = False):
    result = Event().query.filter_by(name = event_name).first()
    if result is None:
        result = Event()
        result.name = event_name
        result.host = host
        result.location = location
        result.description = description
        result.external_link = link
        result.admin_unit = get_admin_unit('Stadt Goslar')
        result.verified = verified
        eventDate = EventDate(event_id = result.id, start=start)
        result.dates.append(eventDate)
        db.session.add(result)
    return result

def has_admin_unit_member_permission(admin_unit_id, permission):
    admin_unit_member = AdminUnitMember.query.filter_by(admin_unit_id=admin_unit_id, user_id=current_user.id).first()
    if admin_unit_member is not None:
        for role in admin_unit_member.roles:
            if permission in role.get_permissions():
                return True

    return False

def can_list_admin_unit_members(admin_unit):
    if not current_user.is_authenticated:
        return False

    # User permission, e.g. user is global admin
    user_perm = Permission(FsPermNeed('admin_unit.members:read'))
    if user_perm.can():
        return True

    if has_admin_unit_member_permission(admin_unit.id, 'admin_unit.members:read'):
        return True

    return False

def can_list_org_members(organization):
    if not current_user.is_authenticated:
        return False

    # User permission, e.g. user is global admin
    user_perm = Permission(FsPermNeed('organization.members:read'))
    if user_perm.can():
        return True

    return True # todo

def can_verify_event(event):
    if not current_user.is_authenticated:
        return False

    # User permission, e.g. user is global admin
    user_perm = Permission(FsPermNeed('event:verify'))
    if user_perm.can():
        return True

    # Admin unit member permissions (Holger, Artur)
    if has_admin_unit_member_permission(event.admin_unit_id, 'event:verify'):
        return True

    # Event has Admin Unit
    # Admin Unit has organization members with roles with permission 'event:verify'
    # This organization has members with roles with permission 'event:verify'
    # Der aktuelle nutzer muss unter diesen nutzern sein
    admin_unit_orgs = AdminUnitOrg.query.filter_by(admin_unit_id=event.admin_unit_id).all()
    for admin_unit_org in admin_unit_orgs:
        for admin_unit_org_role in admin_unit_org.roles:
            if 'event:verify' in admin_unit_org_role.get_permissions():
                org_member = OrgMember.query.filter_by(organization_id=admin_unit_org.organization_id, user_id=current_user.id).first()
                if org_member is not None:
                    for org_member_role in org_member.roles:
                        if 'event:verify' in org_member_role.get_permissions():
                            return True

    return False

@app.before_first_request
def create_user():
    # Admin units
    goslar = upsert_admin_unit('Stadt Goslar')
    upsert_admin_unit('Bad Harzburg')
    upsert_admin_unit('Clausthal')
    upsert_admin_unit('Walkenried')
    upsert_admin_unit('Bad Lauterberg')
    upsert_admin_unit('Harzgerode')
    upsert_admin_unit('Ilsenburg')
    upsert_admin_unit('Osterode')
    upsert_admin_unit('Quedlinburg')
    upsert_admin_unit('Wernigerode')
    upsert_admin_unit('Halberstadt')
    upsert_admin_unit('Wennigsen')
    upsert_admin_unit('Hildesheim')

    # Organizations
    admin_unit_org_event_verifier_role = upsert_admin_unit_org_role('event_verifier', ['event:verify'])
    gmg = upsert_organization("GOSLAR marketing gmbh")
    gz = upsert_organization("Goslarsche Zeitung")

    gmg_admin_unit_org = add_organization_to_admin_unit(gmg, goslar)
    add_role_to_admin_unit_org(gmg_admin_unit_org, admin_unit_org_event_verifier_role)

    gz_admin_unit_org = add_organization_to_admin_unit(gz, goslar)
    add_role_to_admin_unit_org(gz_admin_unit_org, admin_unit_org_event_verifier_role)

    # Users
    admin_role = user_datastore.find_or_create_role("admin")
    admin_role.add_permissions(["user:create", "event:verify", "admin_unit.members:read", "organization.members:read"])

    admin_unit_admin_role = upsert_admin_unit_member_role('admin', ["admin_unit.members:read"])
    admin_unit_event_verifier_role = upsert_admin_unit_member_role('event_verifier', ["event:verify"])
    org_member_event_verifier_role = upsert_org_member_role('event_verifier', ["event:verify"])

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

    # Events
    berlin = pytz.timezone('Europe/Berlin')
    upsert_event("Vienenburger Seefest",
        "Stadt Goslar",
        "Vienenburger See",
        create_berlin_date(2020, 8, 14, 17, 0),
        'Vom 14. bis 16. August 2020 findet im ausgewiesenen Naherholungsgebiet am Fuße des Harzes, dem Goslarer Ortsteil Vienenburg, das Seefest unter dem Motto „Feuer & Wasser“ statt.',
        'https://www.goslar.de/kultur-freizeit/veranstaltungen/156-vienenburger-seefest?layout=*',
        True)

    upsert_event("Tausend Schritte durch die Altstadt",
        "Stadt Goslar",
        "Tourist-Information Goslar",
        create_berlin_date(2020, 9, 1, 10, 0),
        'Tausend Schritte durch die Altstadt Erleben Sie einen geführten Stadtrundgang durch den historischen Stadtkern. Lassen Sie sich von Fachwerkromantik und kaiserlichen Bauten inmitten der UNESCO-Welterbestätte verzaubern. ganzjährig (außer 01.01.) täglich 10:00 Uhr Treffpunkt: Tourist-Information am Marktplatz (Dauer ca. 2 Std.) Erwachsene 8,00 Euro Inhaber Gastkarte Goslar/Kurkarte Hahnenklee 7,00 Euro Schüler/Studenten 6,00 Euro')

    upsert_event("Spaziergang am Nachmittag",
        "Stadt Goslar",
        "Tourist-Information Goslar",
        create_berlin_date(2020, 9, 1, 13, 30),
        'Spaziergang am Nachmittag Begeben Sie sich auf einen geführten Rundgang durch die historische Altstadt. Entdecken Sie malerische Fachwerkgassen und imposante Bauwerke bei einem Streifzug durch das UNESCO-Weltkulturerbe. April – Oktober und 25.11. – 30.12. Montag – Samstag 13:30 Uhr Treffpunkt: Tourist-Information am Marktplatz (Dauer ca. 1,5 Std.) Erwachsene 7,00 Euro Inhaber Gastkarte Goslar/Kurkarte Hahnenklee 6,00 Euro Schüler/Studenten 5,00 Euro')

    upsert_event("Ein Blick hinter die Kulissen - Rathausbaustelle",
        "Stadt Goslar",
        "Nagelkopf am Rathaus",
        create_berlin_date(2020, 9, 3, 17, 0),
        'Allen interessierten Bürgern wird die Möglichkeit geboten, unter fachkundiger Führung des Goslarer Gebäudemanagement (GGM) einen Blick hinter die Kulissen durch das derzeit gesperrte historische Rathaus und die Baustelle Kulturmarktplatz zu werfen. Da bei beiden Führungen die Anzahl der Teilnehmer auf 16 Personen begrenzt ist, ist eine Anmeldung unbedingt notwendig sowie festes Schuhhwerk. Bitte melden Sie sich bei Interesse in der Tourist-Information (Tel. 05321-78060) an. Kinder unter 18 Jahren sind aus Sicherheitsgründen auf der Baustelle nicht zugelassen.')

    upsert_event("Wöltingerode unter Dampf",
        "Kloster Wöltingerode",
        "Kloster Wöltingerode",
        create_berlin_date(2020, 9, 5, 12, 0),
        'Mit einem ländlichen Programm rund um historische Trecker und Landmaschinen, köstliche Produkte aus Brennerei und Region, einem Kunsthandwerkermarkt und besonderen Führungen findet das Hoffest auf dem Klostergut statt.',
        'https://www.woelti-unter-dampf.de')

    upsert_event("Altstadtfest",
        "GOSLAR marketing gmbh",
        "Goslar",
        create_berlin_date(2020, 9, 11, 15, 0),
        'Drei Tage lang dürfen sich die Besucher des Goslarer Altstadtfestes auf ein unterhaltsames und abwechslungsreiches Veranstaltungsprogramm freuen. Der Flohmarkt auf der Kaiserpfalzwiese lädt zum Stöbern vor historischer Kulisse ein.',
        'https://www.goslar.de/kultur-freizeit/veranstaltungen/altstadtfest')

    upsert_event("Adventsmarkt auf der Vienenburg",
        "Vienenburg",
        "Vienenburg",
        create_berlin_date(2020, 12, 13, 12, 0),
        'Inmitten der mittelalterlichen Burg mit dem restaurierten Burgfried findet der „Advent auf der Burg“ statt. Der Adventsmarkt wird von gemeinnützigen und sozialen Vereinen sowie den Kirchen ausgerichtet.')

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
        admin_units=AdminUnit.query.all())

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
        organizations=Organization.query.all())

@app.route('/organization/<int:organization_id>')
def organization(organization_id):
    organization = Organization.query.filter_by(id = organization_id).first()
    current_user_member = OrgMember.query.with_parent(organization).filter_by(user_id = current_user.id).first() if current_user.is_authenticated else None

    return render_template('organization.html',
        organization=organization,
        current_user_member=current_user_member,
        can_list_members=can_list_org_members(organization))

@app.route("/profile")
@auth_required()
def profile():
    return render_template('profile.html')

@app.route("/events")
def events():
    events = Event.query.all()
    return render_template('events.html', events=events)

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

from forms.create_event import CreateEventForm

@app.route("/events/create", methods=('GET', 'POST'))
def create_event():
    form = CreateEventForm()
    if form.validate_on_submit():
        event = Event()
        form.populate_obj(event)
        event.admin_unit = get_admin_unit('Stadt Goslar')
        eventDate = EventDate(event_id = event.id, start=form.start.data)
        event.dates.append(eventDate)
        db.session.commit()
        return redirect(url_for('events'))
    return render_template('create_event.html', form=form)

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