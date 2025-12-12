from project.models.mixins.api_key_owner_mixin_generated import (
    ApiKeyOwnerGeneratedMixin,
)


class ApiKeyOwnerMixin(ApiKeyOwnerGeneratedMixin):
    # api_keys = relationship("ApiKey")

    def allows_another_api_key(self):
        return self.get_number_of_api_keys() < self.max_api_keys

    def get_number_of_api_keys(self):  # pragma: no cover
        raise NotImplementedError()
