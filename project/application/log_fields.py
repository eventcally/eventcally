REDACTED = "[redacted]"

_SECRET_KEYS = {"key", "key_hash"}
_SECRET_PARTS = ("password", "secret", "token")


def message_log_fields(kind: str, message) -> dict:
    fields = {"message_kind": kind, "message_type": type(message).__name__}
    actor = getattr(message, "actor", None)
    if actor is not None:
        fields["actor_user_id"] = actor.user_id
        fields["actor_app_installation_id"] = actor.app_installation_id
    return fields


def message_payload(message) -> dict:
    return _redact(message.model_dump(mode="json"))


def _is_secret_key(key) -> bool:
    name = str(key).lower()
    return name in _SECRET_KEYS or any(part in name for part in _SECRET_PARTS)


def _redact(value):
    if isinstance(value, dict):
        return {
            k: REDACTED if _is_secret_key(k) else _redact(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value
