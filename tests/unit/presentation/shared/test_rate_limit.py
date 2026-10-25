from project.presentation.shared import rate_limit


class _Provider:
    def get_rate_limit_key(self):
        return "key-1"

    def get_rate_limit_value(self):
        return "5/minute"


def test_decorator_uses_the_providers_value_scope_and_key(monkeypatch):
    calls = {}

    def shared_limit(value, scope, key_func):
        calls.update(value=value, scope=scope, key=key_func())
        return "decorator"

    monkeypatch.setattr(rate_limit.limiter, "shared_limit", shared_limit)

    assert rate_limit.get_limit_decorator_for_provider(_Provider()) == "decorator"
    assert calls == {"value": "5/minute", "scope": "api", "key": "key-1"}
