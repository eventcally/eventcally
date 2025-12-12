from project.models.mixins.rate_limit_holder_mixin_generated import (
    RateLimitHolderGeneratedMixin,
)
from project.models.mixins.rate_limit_provider_mixin import RateLimitProviderMixin


class RateLimitHolderMixin(RateLimitHolderGeneratedMixin, RateLimitProviderMixin):
    def get_rate_limit_key(self):
        return f"{self.__tablename__}-{self.id}"

    def get_rate_limit_value(self):
        return self.rate_limit_value
