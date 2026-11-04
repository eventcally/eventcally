from typing import Protocol

from flask_limiter.extension import LimitDecorator

from project.infrastructure.extensions import limiter

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


def rate_limit_rows(provider: RateLimitProvider) -> list[str]:
    """One line per limit of the provider: the limit and its remaining requests."""
    rows = []
    limit_group = get_limit_decorator_for_provider(provider).limit_group
    for limit in limit_group:
        key = limit_group.key_function()
        args = [key, limit.scope_for("", "")]
        stats = limiter.limiter.get_window_stats(limit.limit, *args)
        rows.append(f"{limit.limit}: {stats.remaining} remaining")

    return rows
