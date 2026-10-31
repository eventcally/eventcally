from typing import List, Optional

from pydantic import BaseModel

from project.application.commands.base import Command
from project.application.log_fields import REDACTED, message_log_fields, message_payload
from project.domain.models.entities.actor import Actor


class _Inner(BaseModel):
    api_token: str = "t"
    label: str = "visible"


class _Cmd(Command):
    name: str = "n"
    key: str = "abc"
    key_hash: str = "hash"
    client_secret: str = "s"
    Password_Repeat: str = "p"
    keyboard: str = "kept"
    inner: _Inner = _Inner()
    items: List[_Inner] = [_Inner()]
    note: Optional[str] = None


class _NoActor:
    pass


def test_fields_with_actor():
    cmd = _Cmd(actor=Actor(user_id=3))

    assert message_log_fields("command", cmd) == {
        "message_kind": "command",
        "message_type": "_Cmd",
        "actor_user_id": 3,
        "actor_app_installation_id": None,
    }


def test_fields_without_actor():
    assert message_log_fields("event", _NoActor()) == {
        "message_kind": "event",
        "message_type": "_NoActor",
    }


def test_payload_redacts_secrets_nested_and_in_lists():
    payload = message_payload(_Cmd(actor=Actor(user_id=3)))

    assert payload["name"] == "n"
    assert payload["keyboard"] == "kept"
    assert payload["key"] == REDACTED
    assert payload["key_hash"] == REDACTED
    assert payload["client_secret"] == REDACTED
    assert payload["Password_Repeat"] == REDACTED
    assert payload["inner"] == {"api_token": REDACTED, "label": "visible"}
    assert payload["items"] == [{"api_token": REDACTED, "label": "visible"}]
    assert payload["actor"]["user_id"] == 3
