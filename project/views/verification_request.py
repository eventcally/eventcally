from flask import flash, g, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import access_or_401, get_admin_unit_members_with_permission
from project.forms.verification_request import (
    CreateAdminUnitVerificationRequestForm,
    DeleteVerificationRequestForm,
)
from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)
from project.models.admin_unit import AdminUnit
from project.services.admin_unit import get_admin_unit_query
from project.services.search_params import (
    AdminUnitSearchParams,
    AdminUnitVerificationRequestSearchParams,
)
from project.services.verification import (
    admin_unit_can_verify_admin_unit,
    get_verification_requests_incoming_query,
    get_verification_requests_outgoing_query,
)
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleSqlError,
    manage_required,
    non_match_for_deletion,
    send_mails_async,
)


@app.route("/manage/admin_unit/<int:id>/verification_requests/incoming")
@auth_required()
@manage_required("verification_request:read")
def manage_admin_unit_verification_requests_incoming(id):
    admin_unit = g.manage_admin_unit

    params = AdminUnitVerificationRequestSearchParams()
    params.target_admin_unit_id = admin_unit.id
    requests = get_verification_requests_incoming_query(params).paginate()

    return render_template(
        "manage/verification_requests_incoming.html",
        admin_unit=admin_unit,
        requests=requests.items,
        pagination=get_pagination_urls(requests, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/verification_requests/outgoing")
@auth_required()
@manage_required("verification_request:read")
def manage_admin_unit_verification_requests_outgoing(id):
    admin_unit = g.manage_admin_unit

    params = AdminUnitVerificationRequestSearchParams()
    params.target_admin_unit_id = admin_unit.id
    requests = get_verification_requests_outgoing_query(params).paginate()

    if not admin_unit.is_verified and requests.total == 0:
        return redirect(
            url_for(
                "manage_admin_unit_verification_requests_outgoing_create_select",
                id=admin_unit.id,
            )
        )

    return render_template(
        "manage/verification_requests_outgoing.html",
        admin_unit=admin_unit,
        requests=requests.items,
        pagination=get_pagination_urls(requests, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/verification_requests/outgoing/create/select")
@auth_required()
@manage_required("verification_request:create")
def manage_admin_unit_verification_requests_outgoing_create_select(id):
    admin_unit = g.manage_admin_unit

    params = AdminUnitSearchParams()
    params.only_verifier = True
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
                    "manage_admin_unit_verification_requests_outgoing",
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


@app.route("/verification_request/<int:id>/delete", methods=("GET", "POST"))
@auth_required()
def admin_unit_verification_request_delete(id):
    request = AdminUnitVerificationRequest.query.get_or_404(id)
    access_or_401(request.source_admin_unit, "verification_request:delete")

    form = DeleteVerificationRequestForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.name.data, request.target_admin_unit.name):
            flash(gettext("Entered name does not match organization name"), "danger")
        else:
            try:
                db.session.delete(request)
                db.session.commit()
                flash(gettext("Verification request successfully deleted"), "success")
                return redirect(
                    url_for(
                        "manage_admin_unit_verification_requests_outgoing",
                        id=request.source_admin_unit.id,
                    )
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "verification_request/delete.html", form=form, verification_request=request
    )


def send_member_verification_request_verify_mails(
    admin_unit_id, subject, template, **context
):
    # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
    members = get_admin_unit_members_with_permission(
        admin_unit_id, "verification_request:verify"
    )
    emails = list(map(lambda member: member.user.email, members))

    send_mails_async(emails, subject, template, **context)


def send_verification_request_inbox_mails(request):
    send_member_verification_request_verify_mails(
        request.target_admin_unit_id or request.target_admin_unit.id,
        gettext("New verification request"),
        "verification_request_notice",
        request=request,
    )
