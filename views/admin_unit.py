from app import app, db
from flask import url_for, render_template, request, redirect, flash
from flask_babelex import gettext
from flask_security import auth_required, current_user
from models import AdminUnitMemberInvitation
from sqlalchemy.exc import SQLAlchemyError
from access import get_admin_unit_for_manage_or_404, access_or_401, has_access
from forms.admin_unit import CreateAdminUnitForm, UpdateAdminUnitForm
from .utils import upsert_image_with_data, handleSqlError, permission_missing, flash_errors
from models import AdminUnit, Location, EventOrganizer
from services.admin_unit import add_user_to_admin_unit_with_roles
from services.location import assign_location_values

def update_admin_unit_with_form(admin_unit, form):
    form.populate_obj(admin_unit)

@app.route("/admin_unit/create", methods=('GET', 'POST'))
@auth_required()
def admin_unit_create():
    form = CreateAdminUnitForm()

    if form.validate_on_submit():
        admin_unit = AdminUnit()
        admin_unit.location = Location()
        update_admin_unit_with_form(admin_unit, form)

        try:
            db.session.add(admin_unit)

            # Aktuellen Nutzer als Admin hinzufügen
            add_user_to_admin_unit_with_roles(current_user, admin_unit, ['admin', 'event_verifier'])
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
    else:
        flash_errors(form)

    return render_template('admin_unit/create.html', form=form)

@app.route('/admin_unit/<int:id>/update', methods=('GET', 'POST'))
@auth_required()
def admin_unit_update(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    if not has_access(admin_unit, 'admin_unit:update'):
        return permission_missing(url_for('manage_admin_unit', id=admin_unit.id))

    form = UpdateAdminUnitForm(obj=admin_unit)

    if form.validate_on_submit():
        update_admin_unit_with_form(admin_unit, form)

        try:
            db.session.commit()
            flash(gettext('AdminUnit successfully updated'), 'success')
            return redirect(url_for('admin_unit_update', id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('admin_unit/update.html',
        form=form,
        admin_unit=admin_unit)