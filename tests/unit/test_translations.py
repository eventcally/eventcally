import ast
import enum
import gettext
import importlib
import inspect
import pkgutil
from io import BytesIO
from pathlib import Path

import pytest
from babel.messages.extract import extract_from_dir
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from project.domain import errors
from project.domain.models import enums as domain_enums

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = ["project/domain", "project/application"]
TRANSLATIONS = ROOT / "project" / "translations"
ERROR_NAMES = set(errors.__all__)


def _call_name(node: ast.Call):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _is_str_constant(node) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def test_domain_error_messages_are_marked_for_translation():
    offenders = []
    for source_dir in SOURCE_DIRS:
        for path in sorted((ROOT / source_dir).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            rel = path.relative_to(ROOT)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _call_name(node) in ERROR_NAMES:
                    args = list(node.args[:1]) + [
                        k.value for k in node.keywords if k.arg == "message"
                    ]
                    if any(_is_str_constant(a) for a in args):
                        offenders.append(f"{rel}:{node.lineno}")
                elif isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if (
                            isinstance(stmt, ast.Assign)
                            and any(
                                isinstance(t, ast.Name) and t.id == "default_message"
                                for t in stmt.targets
                            )
                            and _is_str_constant(stmt.value)
                        ):
                            offenders.append(f"{rel}:{stmt.lineno}")

    assert not offenders, "Unmarked error messages: " + ", ".join(offenders)


def test_domain_error_messages_have_german_translation():
    de = gettext.GNUTranslations(
        (TRANSLATIONS / "de" / "LC_MESSAGES" / "messages.mo").open("rb")
    )
    msgids = set()
    for source_dir in SOURCE_DIRS:
        for _, _, message, _, _ in extract_from_dir(
            str(ROOT / source_dir),
            method_map=[("**.py", "python")],
            keywords={"dummy_gettext": None},
        ):
            msgids.add(message)

    assert msgids, "no domain/application messages were extracted"
    untranslated = sorted(m for m in msgids if de.gettext(m) == m)
    assert not untranslated, f"Missing German translations: {untranslated}"


# `bff/manage/verification_requests.py` (STATUS_ENUM_NAME / REASON_ENUM_NAME) localizes
# these enums under their old names; importing it here would pull in the container.
ENUM_MSGID_ALIASES = {
    "OrganizationVerificationRequestReviewStatus": "AdminUnitVerificationRequestReviewStatus",
    "OrganizationVerificationRequestRejectionReason": "AdminUnitVerificationRequestRejectionReason",
}


def _domain_enums():
    for module_info in pkgutil.iter_modules(domain_enums.__path__):
        module = importlib.import_module(f"{domain_enums.__name__}.{module_info.name}")
        for value in vars(module).values():
            if (
                inspect.isclass(value)
                and issubclass(value, enum.Enum)
                and value.__module__ == module.__name__
            ):
                yield value


@pytest.mark.parametrize("locale", ["de", "en"])
def test_domain_enum_members_have_translations(locale):
    """`get_localized_enum_name` builds "<Enum>.<member>" at runtime; a member without a
    translation shows up as that raw msgid (e.g. a status badge "EventStatus.scheduled").
    """
    with (TRANSLATIONS / locale / "LC_MESSAGES" / "messages.mo").open("rb") as f:
        catalog = gettext.GNUTranslations(f)

    enums = list(_domain_enums())
    assert enums, "no domain enums were found"

    missing = []
    for enum_class in enums:
        prefix = ENUM_MSGID_ALIASES.get(enum_class.__name__, enum_class.__name__)
        for member in enum_class:
            msgid = f"{prefix}.{member.name}"
            if catalog.gettext(msgid) == msgid:
                missing.append(msgid)

    assert not missing, f"Missing {locale} translations: {sorted(missing)}"


@pytest.mark.parametrize("locale", ["de", "en"])
def test_compiled_catalogs_match_po(locale):
    base = TRANSLATIONS / locale / "LC_MESSAGES"
    with (base / "messages.po").open("rb") as f:
        catalog = read_po(f, locale=locale)
    buffer = BytesIO()
    write_mo(buffer, catalog)
    buffer.seek(0)
    expected = gettext.GNUTranslations(buffer)._catalog
    with (base / "messages.mo").open("rb") as f:
        actual = gettext.GNUTranslations(f)._catalog

    assert actual == expected, "messages.mo is out of date, run compile.sh"
