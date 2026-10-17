from typing import Protocol

from flask_limiter.extension import LimitDecorator

from project.extensions import limiter

api_rate_limit_scope = "api"


class RateLimitProvider(Protocol):
    def get_rate_limit_key(self) -> str:  # pragma: no cover
        ...

    def get_rate_limit_value(self) -> str:  # pragma: no cover
        ...


def get_limit_decorator_for_provider(
    provider: RateLimitProvider,
) -> LimitDecorator:
    key = provider.get_rate_limit_key()
    return limiter.shared_limit(
        provider.get_rate_limit_value(),
        scope=api_rate_limit_scope,
        key_func=lambda: key,
    )
