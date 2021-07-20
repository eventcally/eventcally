from flask import render_template
from flask_security import auth_required, current_user

from project import app
from project.models import AdminUnitMember
from project.services.admin_unit import get_admin_unit_member_invitations


@app.route("/profile")
@auth_required()
def profile():
    admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
    invitations = get_admin_unit_member_invitations(current_user.email)

    return render_template(
        "profile.html", admin_unit_members=admin_unit_members, invitations=invitations
    )
