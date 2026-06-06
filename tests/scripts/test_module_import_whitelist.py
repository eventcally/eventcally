from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_script_module():
    script_path = (
        Path(__file__).resolve().parents[2] / ".scripts" / "module_import_whitelist.py"
    )
    spec = spec_from_file_location("module_import_whitelist", script_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_collects_all_top_level_and_function_imports(tmp_path):
    module = _load_script_module()
    source = tmp_path / "sample.py"
    source.write_text(
        "\n".join(
            [
                "import os",
                "import targetpkg.alpha",
                "",
                "def outer():",
                "    import targetpkg.beta",
                "    from targetpkg import gamma",
                "",
                "async def async_fn():",
                "    from targetpkg.sub import thing",
            ]
        )
    )

    hits, errors = module.collect_imports([str(tmp_path)], excluded_dirs=set())

    assert errors == []
    assert [hit.import_path for hit in hits] == [
        "os",
        "targetpkg.alpha",
        "targetpkg.beta",
        "targetpkg.gamma",
        "targetpkg.sub.thing",
    ]
    assert [hit.context for hit in hits] == [
        "top-level",
        "top-level",
        "function:outer",
        "function:outer",
        "function:async_fn",
    ]


def test_whitelist_allows_module_prefixes():
    module = _load_script_module()
    allowlist = {"pydantic", "targetpkg.sub.*"}

    assert module.is_allowed("pydantic", allowlist)
    assert module.is_allowed("pydantic.fields", allowlist)
    assert module.is_allowed("targetpkg.sub.thing", allowlist)
    assert not module.is_allowed("targetpkg.beta", allowlist)


def test_load_allowlist_for_path_reads_allowed_imports_cfg(tmp_path):
    module = _load_script_module()
    allowlist_file = tmp_path / "allowed_imports.cfg"
    allowlist_file.write_text("pydantic\n# comment\ntargetpkg.sub.*\n")

    allowlist = module.load_allowlist_for_path(str(tmp_path))

    assert allowlist == {"pydantic", "targetpkg.sub.*"}


def test_main_uses_allowed_imports_cfg_for_scanned_folder(tmp_path, capsys):
    module = _load_script_module()
    source = tmp_path / "sample.py"
    source.write_text(
        "\n".join(
            [
                "import pydantic",
                "def run():",
                "    import targetpkg.beta",
            ]
        )
    )
    allowlist_file = tmp_path / "allowed_imports.cfg"
    allowlist_file.write_text("pydantic\n")

    exit_code = module.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert f"Scanned path: {tmp_path}" in out
    assert "Disallowed imports: 1" in out
    assert "targetpkg.beta" in out
    assert "pydantic" not in out.split("Disallowed import hits:", 1)[-1]


def test_main_evaluates_paths_individually(tmp_path, capsys):
    module = _load_script_module()
    path_one = tmp_path / "one"
    path_two = tmp_path / "two"
    path_one.mkdir()
    path_two.mkdir()

    (path_one / "allowed_imports.cfg").write_text("pydantic\n")
    (path_two / "allowed_imports.cfg").write_text("requests\n")

    (path_one / "a.py").write_text("import pydantic\n")
    (path_two / "b.py").write_text("import requests\n")

    exit_code = module.main([str(path_one), str(path_two)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert f"Scanned path: {path_one}" in out
    assert f"Scanned path: {path_two}" in out
    assert out.count("Disallowed imports: 0") == 2


def test_main_errors_when_allowed_imports_cfg_is_missing(tmp_path):
    module = _load_script_module()

    try:
        module.main([str(tmp_path)])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        assert False, "Expected main() to exit when allowlist file is missing"
