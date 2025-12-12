class RateLimitProviderMixin:
    def get_rate_limit_key(self):  # pragma: no cover
        raise NotImplementedError()

    def get_rate_limit_value(self):  # pragma: no cover
        raise NotImplementedError()
