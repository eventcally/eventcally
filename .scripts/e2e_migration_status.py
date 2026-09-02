#!/usr/bin/env python3
"""Report how far the Cypress -> Playwright e2e migration has progressed.

Purely informational: it prints a markdown table of ported vs. remaining specs
and always exits 0. Duplication between ``cypress/e2e`` and ``e2e/tests`` is the
intended state during the overlap, so there is nothing here to enforce -- what
is wanted is visibility into how much is left.

Delete this script at Stage 4, together with the Cypress suite.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CYPRESS_SPEC_DIR = REPO_ROOT / "cypress" / "e2e"
PLAYWRIGHT_SPEC_DIR = REPO_ROOT / "e2e" / "tests"


def spec_names(directory: Path, suffix: str) -> set[str]:
    """Return the spec base names in *directory*, without *suffix*."""
    return {path.name[: -len(suffix)] for path in sorted(directory.glob(f"*{suffix}"))}


def main() -> int:
    cypress_specs = spec_names(CYPRESS_SPEC_DIR, ".cy.js")
    playwright_specs = spec_names(PLAYWRIGHT_SPEC_DIR, ".spec.js")

    ported = sorted(cypress_specs & playwright_specs)
    remaining = sorted(cypress_specs - playwright_specs)
    extra = sorted(playwright_specs - cypress_specs)

    print("## e2e migration status")
    print()
    print(f"**{len(ported)}/{len(cypress_specs)} ported**")
    print()
    print("| Spec | Cypress | Playwright |")
    print("| --- | --- | --- |")

    for name in sorted(cypress_specs | playwright_specs):
        in_cypress = "✅" if name in cypress_specs else "—"
        in_playwright = "✅" if name in playwright_specs else "—"
        print(f"| `{name}` | {in_cypress} | {in_playwright} |")

    print()

    if remaining:
        print(f"Remaining: {', '.join(f'`{name}`' for name in remaining)}")
    else:
        print("Remaining: none — every Cypress spec has a Playwright counterpart.")

    if extra:
        print()
        print(
            f"Playwright-only (new specs): {', '.join(f'`{name}`' for name in extra)}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
