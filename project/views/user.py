from flask import render_template
from flask_security import auth_required, current_user

from project import app
from project.models import AdminUnitMember, AdminUnitMemberInvitation


@app.route("/profile")
@auth_required()
def profile():
    admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
    invitations = AdminUnitMemberInvitation.query.filter(
        AdminUnitMemberInvitation.email == current_user.email
    ).all()

    return render_template(
        "profile.html", admin_unit_members=admin_unit_members, invitations=invitations
    )
