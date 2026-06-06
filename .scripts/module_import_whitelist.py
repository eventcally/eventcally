#!/usr/bin/env python3
"""Collect and validate imports inside Python files using AST analysis."""

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "env",
    "htmlcov",
    "node_modules",
    "tmp",
    "__pycache__",
}


@dataclass(frozen=True)
class ImportHit:
    file_path: Path
    line: int
    column: int
    context: str
    import_kind: str
    import_path: str


class ImportCollector(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.function_stack: list[str] = []
        self.hits: list[ImportHit] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.hits.append(
                ImportHit(
                    file_path=self.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    context=self._context_label(),
                    import_kind="import",
                    import_path=alias.name,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if node.level != 0 or not module:
            self.generic_visit(node)
            return

        for alias in node.names:
            import_path = f"{module}.{alias.name}"
            self.hits.append(
                ImportHit(
                    file_path=self.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    context=self._context_label(),
                    import_kind="from",
                    import_path=import_path,
                )
            )
        self.generic_visit(node)

    def _context_label(self) -> str:
        if not self.function_stack:
            return "top-level"
        return "function:" + ".".join(self.function_stack)


def parse_allowlist(entries: Sequence[str], allowlist_file: str | None) -> set[str]:
    allowlist = {entry.strip() for entry in entries if entry.strip()}
    if not allowlist_file:
        return allowlist

    path = Path(allowlist_file)
    for line in path.read_text().splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            allowlist.add(value)
    return allowlist


def _allowlist_file_for_path(raw_path: str) -> Path:
    path = Path(raw_path)
    root = path.parent if path.is_file() else path
    return root / "allowed_imports.cfg"


def load_allowlist_for_path(raw_path: str) -> set[str]:
    allowlist_file = _allowlist_file_for_path(raw_path)
    if not allowlist_file.exists():
        raise FileNotFoundError(f"Missing allowlist file: {allowlist_file}")
    return parse_allowlist([], str(allowlist_file))


def is_allowed(import_path: str, allowlist: set[str]) -> bool:
    for rule in allowlist:
        if import_path == rule or import_path.startswith(f"{rule}."):
            return True
        if rule.endswith(".*"):
            prefix = rule[:-2]
            if import_path == prefix or import_path.startswith(f"{prefix}."):
                return True
    return False


def iter_python_files(paths: Sequence[str], excluded_dirs: set[str]) -> Iterator[Path]:
    for raw_path in paths:
        base = Path(raw_path)
        if not base.exists():
            continue
        if base.is_file() and base.suffix == ".py":
            yield base
            continue

        for file_path in base.rglob("*.py"):
            if any(part in excluded_dirs for part in file_path.parts):
                continue
            yield file_path


def collect_imports(
    paths: Sequence[str],
    excluded_dirs: set[str] | None = None,
) -> tuple[list[ImportHit], list[tuple[Path, str]]]:
    excluded = excluded_dirs or DEFAULT_EXCLUDED_DIRS
    hits: list[ImportHit] = []
    parse_errors: list[tuple[Path, str]] = []

    for file_path in iter_python_files(paths, excluded):
        try:
            source = file_path.read_text()
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append((file_path, str(exc)))
            continue

        collector = ImportCollector(file_path=file_path)
        collector.visit(tree)
        hits.extend(collector.hits)

    hits.sort(
        key=lambda item: (str(item.file_path), item.line, item.column, item.import_path)
    )
    return hits, parse_errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect imports from a folder and validate them against a whitelist."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to scan.",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        metavar="DIR_NAME",
        help="Directory name to exclude while scanning (can repeat).",
    )
    return parser


def _render_hits(title: str, hits: Iterable[ImportHit]) -> list[str]:
    lines = [title]
    for hit in hits:
        lines.append(
            f"- {hit.file_path}:{hit.line}:{hit.column + 1} [{hit.context}] "
            f"{hit.import_kind} {hit.import_path}"
        )
    return lines


def evaluate_path(
    path: str, excluded_dirs: set[str]
) -> tuple[list[ImportHit], list[tuple[Path, str]], list[ImportHit]]:
    allowlist = load_allowlist_for_path(path)
    hits, parse_errors = collect_imports(
        paths=[path],
        excluded_dirs=excluded_dirs,
    )
    disallowed = [hit for hit in hits if not is_allowed(hit.import_path, allowlist)]
    return hits, parse_errors, disallowed


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    excluded_dirs = DEFAULT_EXCLUDED_DIRS | {
        entry.strip() for entry in args.exclude_dir
    }
    output: list[str] = []
    has_disallowed = False

    for path in args.paths:
        try:
            hits, parse_errors, disallowed = evaluate_path(path, excluded_dirs)
        except FileNotFoundError as exc:
            parser.error(str(exc))

        output.extend(
            [
                f"Scanned path: {path}",
                f"Scanned imports: {len(hits)}",
                f"Allowed imports: {len(hits) - len(disallowed)}",
                f"Disallowed imports: {len(disallowed)}",
            ]
        )

        if disallowed:
            has_disallowed = True
            output.extend(_render_hits("\nDisallowed import hits:", disallowed))
        else:
            output.append("\nNo matching imports found.")

        if parse_errors:
            output.append("\nFiles skipped due to parse errors:")
            for parse_error_path, error in parse_errors:
                output.append(f"- {parse_error_path}: {error}")

        output.append("")

    print("\n".join(output))
    return 1 if has_disallowed else 0


if __name__ == "__main__":
    sys.exit(main())
