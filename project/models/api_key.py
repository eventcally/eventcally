from sqlalchemy.event import listens_for

from project import db
from project.models.api_key_generated import ApiKeyGeneratedMixin
from project.utils import make_check_violation


class ApiKey(db.Model, ApiKeyGeneratedMixin):
    __default_rate_limit_value__ = "500/hour"

    @property
    def owner(self):  # pragma: no cover
        if self.user:
            return self.user

        if self.admin_unit:
            return self.admin_unit

        if self.user_id:
            from project.models.user import User

            return User.query.get(self.user_id)

        if self.admin_unit_id:
            from project.models.admin_unit import AdminUnit

            return AdminUnit.query.get(self.admin_unit_id)

    def generate_key(self) -> str:
        from project.utils import generate_api_key, hash_api_key

        key = generate_api_key()
        self.key_hash = hash_api_key(key)
        return key

    def check_max_count(self):
        if not self.owner.allows_another_api_key():
            raise make_check_violation(
                "The maximum number of API keys has been reached."
            )


@listens_for(ApiKey, "before_insert")
def before_saving_api_key(mapper, connect, self):
    self.check_max_count()
