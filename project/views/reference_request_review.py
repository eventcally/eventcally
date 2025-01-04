from project.views.utils import send_template_mails_to_admin_unit_members_async


def send_reference_request_review_status_mails(request):
    # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
    send_template_mails_to_admin_unit_members_async(
        request.event.admin_unit_id,
        "reference_request:create",
        "reference_request_review_status_notice",
        request=request,
    )
