#!/usr/bin/env python3
"""Generate and verify the ignore list of the delivery-reads-through-queries contract.

The contract in `.importlinter` forbids `project.views` (including
`project.views.modular`) and `project.api` from importing `project.models`. Every module
that still does is listed in its `ignore_imports`, one line per (importer, imported module) pair. The
list must only shrink: delete an entry as soon as its import is gone.

The import graph comes from grimp, the library import-linter itself uses, so the
generated entries match exactly the edges `lint-imports` checks.

Usage:
    python .scripts/models_import_ignores.py           # print the generated block
    python .scripts/models_import_ignores.py --write   # rewrite .importlinter
    python .scripts/models_import_ignores.py --check   # fail if the list is out of date
"""

import argparse
import sys
from pathlib import Path

import grimp

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / ".importlinter"
CONTRACT_SECTION = "[importlinter:contract:delivery-reads-through-queries]"
IGNORE_KEY = "ignore_imports ="
INDENT = "    "

ROOT_PACKAGE = "project"
SOURCE_PACKAGES = ("project.views", "project.api")
FORBIDDEN_PACKAGE = "project.models"

# Delivery modules that stay on the ORM for good: Flask-Admin, Flask-Security
# login flows and the Authlib OAuth2 integration (see the read-side migration plan).
PERMANENT_EXEMPTIONS = (
    "project.views.flask_admin",
    "project.views.oauth",
)


def _is_in_package(module: str, package: str) -> bool:
    return module == package or module.startswith(f"{package}.")


def collect_entries(graph=None) -> list[str]:
    if graph is None:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        graph = grimp.build_graph(ROOT_PACKAGE)

    entries = set()

    for package in SOURCE_PACKAGES:
        importers = {package} | graph.find_descendants(package)

        for importer in importers:
            for imported in graph.find_modules_directly_imported_by(importer):
                if _is_in_package(imported, FORBIDDEN_PACKAGE):
                    entries.add(f"{importer} -> {imported}")

    return sorted(entries)


def _find_block(lines: list[str]) -> tuple[int, int]:
    """Return the [start, end) line range of the contract's ignore_imports values."""
    try:
        section_start = lines.index(CONTRACT_SECTION)
    except ValueError:
        raise SystemExit(f"{CONTRACT_SECTION} not found in {CONFIG_FILE.name}")

    for index in range(section_start + 1, len(lines)):
        line = lines[index]

        if line.startswith("["):
            break

        if line.strip() == IGNORE_KEY.strip():
            start = index + 1
            end = start

            while end < len(lines) and lines[end].startswith((" ", "\t")):
                end += 1

            return start, end

    raise SystemExit(f"'{IGNORE_KEY}' not found in {CONTRACT_SECTION}")


def read_entries() -> list[str]:
    lines = CONFIG_FILE.read_text().splitlines()
    start, end = _find_block(lines)
    return [line.strip() for line in lines[start:end] if line.strip()]


def write_entries(entries: list[str]) -> None:
    lines = CONFIG_FILE.read_text().splitlines()
    start, end = _find_block(lines)
    lines[start:end] = [f"{INDENT}{entry}" for entry in entries]
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="Rewrite .importlinter.")
    group.add_argument(
        "--check", action="store_true", help="Fail if the ignore list is out of date."
    )
    args = parser.parse_args(argv)

    generated = collect_entries()

    if args.write:
        write_entries(generated)
        print(f"Wrote {len(generated)} ignore entries to {CONFIG_FILE.name}")
        return 0

    if args.check:
        current = read_entries()
        stale = sorted(set(current) - set(generated))
        missing = sorted(set(generated) - set(current))

        for entry in stale:
            print(f"stale (import is gone, delete the entry): {entry}")

        for entry in missing:
            print(f"missing (new models import in delivery code): {entry}")

        if stale:
            print("Run: python .scripts/models_import_ignores.py --write")

        if missing:
            print("Read through the query bus instead of adding an ignore entry.")

        if stale or missing:
            return 1

        print(f"{len(current)} ignore entries, up to date")
        return 0

    for entry in generated:
        print(f"{INDENT}{entry}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
