import datetime

from project.models import User
from project.services.base_service import BaseService
from project.views.utils import send_template_mails_to_users_async


class UserService(BaseService[User]):
    def request_deletion(self, object: User):
        object.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        object.deletion_requested_by_id = self.context_provider.current_user_id_or_none
        self.repo.update_object(object)

        self._send_user_deletion_requested_mail(object)

    def _send_user_deletion_requested_mail(self, user: User):
        send_template_mails_to_users_async(
            [user],
            "user_deletion_requested_notice",
            user=user,
        )
