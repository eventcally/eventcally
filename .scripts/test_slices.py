#!/usr/bin/env python3
"""Test slices: which tests own which part of ``project/``.

A slice is a set of test paths plus the source paths it owns. Every slice run
also includes ``tests/unit`` and must cover its owned paths at 100% on its own,
so a change only needs its slice instead of the full integration suite.

The per-slice check reads one combined coverage file recorded with
``--cov-context=test``; the empty context (module-level lines executed at
import time) always counts.

Usage:
    python .scripts/test_slices.py tests SLICE
    python .scripts/test_slices.py check [--data FILE] [--slice NAME] [--markdown]
    python .scripts/test_slices.py changed [BASE]

Exit codes: 1 when an ENFORCED slice is under 100%, 2 when the slice map does
not own every project file exactly once.
"""

import argparse
import configparser
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

UNIT_TESTS = "tests/unit"
INTEGRATION_TESTS = "tests/integration"

# The ratchet: a slice listed here must stay at 100% on its own (unit tests
# included). Add yours when it gets there.
ENFORCED: list[str] = ["unit", "web", "api", "bff", "misc"]


@dataclass(frozen=True)
class Slice:
    tests: list[str] = field(default_factory=list)
    owns: list[str] = field(default_factory=list)


SLICES: dict[str, Slice] = {
    "unit": Slice(
        tests=[UNIT_TESTS],
        owns=["project/domain/", "project/application/", "project/shared/"],
    ),
    "infra": Slice(
        tests=[
            f"{INTEGRATION_TESTS}/infrastructure",
            f"{INTEGRATION_TESTS}/services",
            f"{INTEGRATION_TESTS}/service_layer",
        ],
        owns=["project/infrastructure/", "project/services/"],
    ),
    "web": Slice(
        tests=[f"{INTEGRATION_TESTS}/presentation/web"],
        owns=["project/presentation/web/"],
    ),
    "api": Slice(
        tests=[f"{INTEGRATION_TESTS}/presentation/api"],
        owns=["project/presentation/api/"],
    ),
    "bff": Slice(
        tests=[f"{INTEGRATION_TESTS}/presentation/bff"],
        owns=["project/presentation/bff/"],
    ),
    "misc": Slice(
        tests=[
            f"{INTEGRATION_TESTS}/presentation/cli",
            f"{INTEGRATION_TESTS}/presentation/tasks",
            f"{INTEGRATION_TESTS}/presentation/shared",
            f"{INTEGRATION_TESTS}/shared",
            f"{INTEGRATION_TESTS}/test_*.py",
        ],
        owns=[
            "project/presentation/cli/",
            "project/presentation/tasks/",
            "project/presentation/shared/",
            "project/presentation/__init__.py",
            "project/*.py",
        ],
    ),
}


def _owns(pattern: str, path: str) -> bool:
    if pattern.endswith("/"):
        return path.startswith(pattern)

    return fnmatch.fnmatchcase(path, pattern) and path.count("/") == pattern.count("/")


def owner_of(path: str) -> str | None:
    """Name of the slice that owns a ``project/`` file, if any."""
    for name, slice_ in SLICES.items():
        if any(_owns(pattern, path) for pattern in slice_.owns):
            return name

    return None


def _test_matches(pattern: str, path: str) -> bool:
    if "*" in pattern:
        return fnmatch.fnmatchcase(path, pattern)

    return path == pattern or path.startswith(pattern + "/")


def slice_of_test(path: str) -> str | None:
    """Name of the slice that holds a test file, if any."""
    for name, slice_ in SLICES.items():
        if any(_test_matches(pattern, path) for pattern in slice_.tests):
            return name

    return None


def omit_patterns() -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(ROOT / ".coveragerc")
    raw = parser.get("run", "omit", fallback="")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def project_files() -> list[str]:
    omits = omit_patterns()
    files = (
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "project").rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return sorted(
        f
        for f in files
        if not any(fnmatch.fnmatchcase(f, pattern) for pattern in omits)
    )


def ownership_problems() -> list[str]:
    """Project files owned by no slice or by more than one."""
    problems = []

    for path in project_files():
        owners = [
            name
            for name, slice_ in SLICES.items()
            if any(_owns(pattern, path) for pattern in slice_.owns)
        ]

        if len(owners) != 1:
            problems.append(f"{path}: owned by {owners or 'no slice'}")

    return problems


def test_paths(name: str) -> list[str]:
    """``tests/unit`` plus the slice's test paths, globs expanded."""
    paths = [UNIT_TESTS]

    for pattern in SLICES[name].tests:
        if pattern == UNIT_TESTS:
            continue

        if "*" in pattern:
            paths.extend(
                sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern))
            )
        else:
            paths.append(pattern)

    return paths


def _contexts(name: str) -> list[str]:
    contexts = ["^$", f"^{re.escape(UNIT_TESTS)}/"]

    for path in test_paths(name)[1:]:
        contexts.append(f"^{re.escape(path)}")

    return contexts


def _slice_report(cov, name: str) -> tuple[int, int, dict[str, str]]:
    """Statements, missed and ``{file: missing lines}`` of one slice."""
    cov.get_data().set_query_contexts(_contexts(name))
    statements = 0
    missed = 0
    missing_by_file: dict[str, str] = {}

    for measured in sorted(cov.get_data().measured_files()):
        rel = Path(measured)
        rel = rel.relative_to(ROOT).as_posix() if rel.is_absolute() else rel.as_posix()

        if not rel.endswith(".py") or owner_of(rel) != name:
            continue

        _, executable, _, missing, formatted = cov.analysis2(measured)
        statements += len(executable)
        missed += len(missing)

        if missing:
            missing_by_file[rel] = formatted

    return statements, missed, missing_by_file


def cmd_tests(args: argparse.Namespace) -> int:
    for path in test_paths(args.slice):
        print(path)

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from coverage import Coverage

    problems = ownership_problems()

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2

    cov = Coverage(
        data_file=str(ROOT / args.data), config_file=str(ROOT / ".coveragerc")
    )
    cov.load()
    names = [args.slice] if args.slice else list(SLICES)
    rows = []
    failed = False

    for name in names:
        statements, missed, missing_by_file = _slice_report(cov, name)
        percent = 100.0 * (statements - missed) / statements if statements else 100.0
        rows.append((name, statements, missed, percent, missing_by_file))

        if name in ENFORCED and missed:
            failed = True

    if args.markdown:
        print("| Slice | Statements | Missed | Cover | Enforced |")
        print("| --- | ---: | ---: | ---: | :---: |")

        for name, statements, missed, percent, _ in rows:
            enforced = "yes" if name in ENFORCED else "no"
            print(f"| {name} | {statements} | {missed} | {percent:.2f}% | {enforced} |")
    else:
        print(f"{'slice':<8}{'statements':>12}{'missed':>8}{'cover':>9}  enforced")

        for name, statements, missed, percent, _ in rows:
            enforced = "yes" if name in ENFORCED else "no"
            print(f"{name:<8}{statements:>12}{missed:>8}{percent:>8.2f}%  {enforced}")

    for name, _, missed, _, missing_by_file in rows:
        if not missed:
            continue

        print(f"\n{name}: {missed} missed")

        for path, lines in missing_by_file.items():
            print(f"  {path}: {lines}")

    if failed:
        print("\nAn enforced slice is under 100%.", file=sys.stderr)
        return 1

    return 0


def _git_lines(*git_args: str) -> list[str]:
    result = subprocess.run(
        ["git", *git_args], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def changed_slices(paths: list[str]) -> list[str]:
    """Slices to run for changed files (coverage ownership, not regression safety)."""
    names: set[str] = set()

    for path in paths:
        if path.startswith("project/"):
            owner = owner_of(path)

            if owner:
                names.add(owner)
        elif path.startswith(f"{UNIT_TESTS}/"):
            names.add("unit")
        elif path.startswith(f"{INTEGRATION_TESTS}/"):
            owner = slice_of_test(path)

            if owner:
                names.add(owner)
            else:
                # conftest, seeder, base classes: shared by every integration slice
                names.update(n for n in SLICES if n != "unit")

    return [name for name in SLICES if name in names]


def cmd_changed(args: argparse.Namespace) -> int:
    paths = set(_git_lines("diff", "--name-only", f"{args.base}...HEAD"))
    paths.update(_git_lines("diff", "--name-only", "HEAD"))
    paths.update(_git_lines("ls-files", "--others", "--exclude-standard"))

    for name in changed_slices(sorted(paths)):
        print(name)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    tests = sub.add_parser("tests", help="print the test paths of a slice")
    tests.add_argument("slice", choices=list(SLICES))
    tests.set_defaults(func=cmd_tests)

    check = sub.add_parser("check", help="per-slice coverage from a combined data file")
    check.add_argument("--data", default=".coverage")
    check.add_argument("--slice", choices=list(SLICES))
    check.add_argument("--markdown", action="store_true")
    check.set_defaults(func=cmd_check)

    changed = sub.add_parser("changed", help="slices touched by the current changes")
    changed.add_argument("base", nargs="?", default="origin/main")
    changed.set_defaults(func=cmd_changed)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
