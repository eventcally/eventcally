from project import app, db
from flask import url_for, render_template, request, redirect, flash
from flask_babelex import gettext
from flask_security import auth_required, current_user
from project.models import AdminUnitMember, AdminUnitMemberRole
from project.forms.admin_unit_member import DeleteAdminUnitMemberForm, UpdateAdminUnitMemberForm
from project.views.utils import permission_missing, send_mail, handleSqlError, flash_errors
from project.access import get_admin_unit_for_manage_or_404, has_access
from project.services.admin_unit import add_roles_to_admin_unit_member
from sqlalchemy.exc import SQLAlchemyError

@app.route('/manage/member/<int:id>/update', methods=('GET', 'POST'))
@auth_required()
def manage_admin_unit_member_update(id):
    member = AdminUnitMember.query.get_or_404(id)
    admin_unit = member.adminunit

    if not has_access(admin_unit, 'admin_unit.members:update'):
        return permission_missing(url_for('manage_admin_unit', id=admin_unit.id))

    form = UpdateAdminUnitMemberForm()
    form.roles.choices = [(c.name, gettext(c.title)) for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()]

    if form.validate_on_submit():
        member.roles.clear()
        add_roles_to_admin_unit_member(member, form.roles.data)

        try:
            db.session.commit()
            flash(gettext('Member successfully updated'), 'success')
            return redirect(url_for('manage_admin_unit_members', id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        form.roles.data = [c.name for c in member.roles]

    return render_template('admin_unit/update_member.html',
        admin_unit=admin_unit,
        member=member,
        form=form)

@app.route('/manage/member/<int:id>/delete', methods=('GET', 'POST'))
@auth_required()
def manage_admin_unit_member_delete(id):
    member = AdminUnitMember.query.get_or_404(id)
    admin_unit = member.adminunit

    if not has_access(admin_unit, 'admin_unit.members:delete'):
        return permission_missing(url_for('manage_admin_unit', id=admin_unit.id))

    form = DeleteAdminUnitMemberForm()

    if form.validate_on_submit():
        if form.email.data != member.user.email:
            flash(gettext('Entered email does not match member email'), 'danger')
        else:
            try:
                db.session.delete(member)
                db.session.commit()
                flash(gettext('Member successfully deleted'), 'success')
                return redirect(url_for('manage_admin_unit_members', id=admin_unit.id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('manage/delete_member.html',
        form=form,
        member=member)