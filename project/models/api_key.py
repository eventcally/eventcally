from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.orm import declared_attr, deferred

from project import db
from project.models.rate_limit_provider_mixin import RateLimitHolderMixin
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class ApiKey(db.Model, TrackableMixin, RateLimitHolderMixin):
    __tablename__ = "apikey"
    __display_name__ = "API key"
    __table_args__ = (
        CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name="apikey_admin_unit_xor_user",
        ),
        UniqueConstraint("name", "admin_unit_id", name="uq_apikey_name_admin_unit_id"),
        UniqueConstraint("name", "user_id", name="uq_apikey_name_user_id"),
    )
    __default_rate_limit_value__ = "500/hour"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)

    admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )

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


class ApiKeyOwnerMixin:
    # api_keys = relationship("ApiKey")

    @declared_attr
    def max_api_keys(cls):
        return deferred(
            db.Column(
                "max_api_keys",
                db.Integer(),
                nullable=False,
                default=1,
                server_default="1",
            ),
        )

    def allows_another_api_key(self):
        return self.get_number_of_api_keys() < self.max_api_keys

    def get_number_of_api_keys(self):  # pragma: no cover
        raise NotImplementedError()
