#!/usr/bin/env python3
"""Print read-side migration metrics as a Markdown table.

Paste the output into each read-slice PR as before/after numbers. Counts are
line-based regex matches, so they are a progress signal, not an exact census.

Usage:
    python .scripts/read_path_report.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = (
    ("web", ROOT / "project" / "presentation" / "web"),
    ("api", ROOT / "project" / "api"),
    ("shared", ROOT / "project" / "presentation" / "shared"),
    ("services", ROOT / "project" / "services"),
    ("oauth2.py", ROOT / "project" / "oauth2.py"),
)

MODELS_IMPORT = re.compile(
    r"^\s*(from project\.infrastructure\.models\b|import project\.infrastructure\.models\b)"
)
METRICS = (
    ("`.query`", re.compile(r"\.query\b")),
    ("`select(`", re.compile(r"\bselect\(")),
    ("`paginate(`", re.compile(r"\bpaginate\(")),
    ("`get_or_404` / `first_or_404`", re.compile(r"\b(get_or_404|first_or_404)\b")),
)


def _python_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    return sorted(p for p in path.rglob("*.py") if "__pycache__" not in p.parts)


def collect(path: Path) -> list[int]:
    files = _python_files(path)
    models_files = 0
    counts = [0] * len(METRICS)

    for file in files:
        lines = file.read_text().splitlines()

        if any(MODELS_IMPORT.match(line) for line in lines):
            models_files += 1

        for index, (_, pattern) in enumerate(METRICS):
            counts[index] += sum(len(pattern.findall(line)) for line in lines)

    return [len(files), models_files, *counts]


def main() -> int:
    headers = ["Target", "Files", "Files importing `project.infrastructure.models`"]
    headers += [label for label, _ in METRICS]
    rows = [[label, *collect(path)] for label, path in TARGETS]

    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join("---" for _ in headers) + "|")

    for row in rows:
        print("| " + " | ".join(str(value) for value in row) + " |")

    return 0


if __name__ == "__main__":
    sys.exit(main())
