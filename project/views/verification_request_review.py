from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import access_or_401, has_access
from project.forms.verification_request import VerificationRequestReviewForm
from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)
from project.services.admin_unit import upsert_admin_unit_relation
from project.views.utils import (
    flash_errors,
    flash_message,
    handleSqlError,
    send_template_mails_to_admin_unit_members_async,
)


@app.route("/verification_request/<int:id>/review", methods=("GET", "POST"))
@auth_required()
def admin_unit_verification_request_review(id):
    request = AdminUnitVerificationRequest.query.get_or_404(id)
    access_or_401(request.target_admin_unit, "verification_request:verify")

    if request.review_status == AdminUnitVerificationRequestReviewStatus.verified:
        flash_message(
            gettext("Verification request already verified"),
            url_for("organizations", path=request.source_admin_unit_id),
            gettext("View organization"),
            "danger",
        )
        return redirect(
            url_for(
                "manage_admin_unit_verification_requests_incoming",
                id=request.target_admin_unit_id,
            )
        )

    form = VerificationRequestReviewForm(obj=request)

    if form.validate_on_submit():
        form.populate_obj(request)

        try:
            if (
                request.review_status
                == AdminUnitVerificationRequestReviewStatus.verified
            ):
                relation = upsert_admin_unit_relation(
                    request.target_admin_unit_id, request.source_admin_unit_id
                )
                relation.verify = True

                if form.auto_verify.data:
                    relation.auto_verify_event_reference_requests = True

                msg = gettext("Organization successfully verified")
            else:
                msg = gettext("Verification request successfully updated")

            db.session.commit()
            send_verification_request_review_status_mails(request)
            flash(msg, "success")
            return redirect(
                url_for(
                    "manage_admin_unit_verification_requests_incoming",
                    id=request.target_admin_unit_id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    form.auto_verify.description = gettext(
        "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
        admin_unit_name=request.source_admin_unit.name,
    )

    return render_template(
        "verification_request/review.html",
        form=form,
        request=request,
    )


@app.route("/verification_request/<int:id>/review_status")
def admin_unit_verification_request_review_status(id):
    request = AdminUnitVerificationRequest.query.get_or_404(id)

    if not has_access(
        request.target_admin_unit, "verification_request:verify"
    ) and not has_access(request.source_admin_unit, "verification_request:create"):
        abort(401)

    return render_template(
        "verification_request/review_status.html",
        verification_request=request,
    )


def send_verification_request_review_status_mails(request):
    # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
    send_template_mails_to_admin_unit_members_async(
        request.source_admin_unit_id,
        "verification_request:create",
        "verification_request_review_status_notice",
        request=request,
    )
