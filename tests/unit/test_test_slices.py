import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

_spec = importlib.util.spec_from_file_location(
    "test_slices", ROOT / ".scripts" / "test_slices.py"
)
test_slices = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(test_slices)


def test_every_project_file_has_exactly_one_owner():
    assert test_slices.ownership_problems() == []


def test_every_integration_test_belongs_to_one_slice():
    integration = ROOT / "tests" / "integration"
    paths = sorted(
        p.relative_to(ROOT).as_posix()
        for p in integration.rglob("test_*.py")
        if "__pycache__" not in p.parts
    )
    assert paths

    for path in paths:
        holders = [
            name
            for name, slice_ in test_slices.SLICES.items()
            if any(test_slices._test_matches(t, path) for t in slice_.tests)
        ]
        assert len(holders) == 1, f"{path}: {holders}"


def test_tests_lists_unit_first_and_expands_globs():
    paths = test_slices.test_paths("misc")
    assert paths[0] == "tests/unit"
    assert "tests/integration/test_factory.py" in paths
    assert not any("*" in p for p in paths)
    assert test_slices.test_paths("bff") == [
        "tests/unit",
        "tests/integration/presentation/bff",
    ]


def test_enforced_names_are_slices():
    assert set(test_slices.ENFORCED) <= set(test_slices.SLICES)


def test_changed_maps_to_owning_slice():
    changed = test_slices.changed_slices
    assert changed(["project/presentation/api/x.py"]) == ["api"]
    assert changed(["project/shared/utils.py"]) == ["unit"]
    assert changed(["project/domain/models/x.py"]) == ["unit"]
    assert changed(["project/factory.py"]) == ["misc"]
    assert changed(["tests/integration/presentation/bff/test_x.py"]) == ["bff"]
    assert changed(["tests/unit/shared/test_x.py"]) == ["unit"]
    assert changed(["README.md", "doc/x.md"]) == []


def test_changed_shared_integration_fixtures_run_every_integration_slice():
    result = test_slices.changed_slices(["tests/integration/conftest.py"])
    assert result == ["infra", "web", "api", "bff", "misc"]
