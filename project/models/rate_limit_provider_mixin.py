from sqlalchemy.orm import declared_attr, deferred

from project import db


class RateLimitProviderMixin:
    def get_rate_limit_key(self):  # pragma: no cover
        raise NotImplementedError()

    def get_rate_limit_value(self):  # pragma: no cover
        raise NotImplementedError()


class RateLimitHolderMixin(RateLimitProviderMixin):
    @declared_attr
    def rate_limit_value(cls):
        return deferred(
            db.Column(
                "rate_limit_value",
                db.String(255),
                nullable=False,
                default=cls.__default_rate_limit_value__,
                server_default=cls.__default_rate_limit_value__,
            ),
        )

    def get_rate_limit_key(self):
        return f"{self.__tablename__}-{self.id}"

    def get_rate_limit_value(self):
        return self.rate_limit_value
