from project.views.utils import send_template_mails_to_admin_unit_members_async


def send_verification_request_review_status_mails(request):
    # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
    send_template_mails_to_admin_unit_members_async(
        request.source_admin_unit_id,
        "verification_request:create",
        "verification_request_review_status_notice",
        request=request,
    )
