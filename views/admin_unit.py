from app import app
from flask import url_for, render_template, request, redirect
from flask_security import auth_required
from models import AdminUnitMemberInvitation
from sqlalchemy.exc import SQLAlchemyError

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