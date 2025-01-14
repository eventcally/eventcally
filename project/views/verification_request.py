from flask import flash, g, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.forms.verification_request import CreateAdminUnitVerificationRequestForm
from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)
from project.models.admin_unit import AdminUnit
from project.services.admin_unit import get_admin_unit_query
from project.services.search_params import AdminUnitSearchParams
from project.services.verification import admin_unit_can_verify_admin_unit
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleSqlError,
    manage_required,
    send_template_mails_to_admin_unit_members_async,
)


@app.route("/manage/admin_unit/<int:id>/verification_requests/outgoing/create/select")
@auth_required()
@manage_required("verification_request:create")
def manage_admin_unit_verification_requests_outgoing_create_select(id):
    admin_unit = g.manage_admin_unit

    params = AdminUnitSearchParams()
    params.only_verifier = True
    params.incoming_verification_requests_postal_code = admin_unit.location.postalCode
    admin_units = get_admin_unit_query(params).paginate()

    return render_template(
        "manage/verification_requests_outgoing_create_select.html",
        admin_unit=admin_unit,
        admin_units=admin_units.items,
        pagination=get_pagination_urls(admin_units, id=id),
    )


@app.route(
    "/manage/admin_unit/<int:id>/verification_requests/outgoing/create/target/<int:target_id>",
    methods=("GET", "POST"),
)
@auth_required()
@manage_required("verification_request:create")
def manage_admin_unit_verification_requests_outgoing_create(id, target_id):
    admin_unit = g.manage_admin_unit
    target_admin_unit = AdminUnit.query.get_or_404(target_id)

    if not admin_unit_can_verify_admin_unit(
        admin_unit, target_admin_unit
    ):  # pragma: no cover
        return redirect(
            url_for(
                "manage_admin_unit_verification_requests_outgoing_create_select",
                id=admin_unit.id,
            )
        )

    form = CreateAdminUnitVerificationRequestForm()

    if form.validate_on_submit():
        request = AdminUnitVerificationRequest()
        form.populate_obj(request)
        request.source_admin_unit = admin_unit
        request.target_admin_unit = target_admin_unit

        try:
            db.session.add(request)

            request.review_status = AdminUnitVerificationRequestReviewStatus.inbox
            send_verification_request_inbox_mails(request)
            msg = gettext(
                "Request successfully created. You will be notified after the other organization reviewed the request."
            )

            db.session.commit()
            flash(msg, "success")
            return redirect(
                url_for(
                    "manage_admin_unit.outgoing_admin_unit_verification_requests",
                    id=admin_unit.id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "manage/verification_requests_outgoing_create.html",
        form=form,
        admin_unit=admin_unit,
        target_admin_unit=target_admin_unit,
    )


def send_verification_request_inbox_mails(request):
    # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
    admin_unit_id = request.target_admin_unit_id or request.target_admin_unit.id
    send_template_mails_to_admin_unit_members_async(
        admin_unit_id,
        "verification_request:verify",
        "verification_request_notice",
        request=request,
    )
