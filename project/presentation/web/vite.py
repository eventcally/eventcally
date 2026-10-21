import json
import os
from typing import Dict, List, Optional, Set

from flask import current_app, url_for
from markupsafe import Markup, escape

# Entry name -> source path (dev server serves the sources directly).
ENTRIES = {
    "admin": "src/apps/admin/main.ts",
    "public": "src/apps/public/main.ts",
}

_MANIFEST_PATH = ("static", "dist", ".vite", "manifest.json")
_manifest_cache: Dict[str, dict] = {}


def _manifest_file() -> str:
    return os.path.join(current_app.root_path, "presentation", "web", *_MANIFEST_PATH)


def _load_manifest() -> Optional[dict]:
    path = _manifest_file()
    debug = current_app.config.get("FLASK_DEBUG")

    if not debug and path in _manifest_cache:
        return _manifest_cache[path]

    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return None

    _manifest_cache[path] = manifest
    return manifest


def _asset_url(file: str) -> str:
    return url_for("static", filename="dist/" + file)


def _collect_imports(manifest: dict, chunk: dict, seen: Set[str]) -> List[dict]:
    chunks = []
    for key in chunk.get("imports", []):
        if key in seen or key not in manifest:
            continue
        seen.add(key)
        imported = manifest[key]
        chunks.append(imported)
        chunks.extend(_collect_imports(manifest, imported, seen))
    return chunks


def _find_entry(manifest: dict, name: str) -> Optional[dict]:
    for chunk in manifest.values():
        if chunk.get("isEntry") and chunk.get("name") == name:
            return chunk
    return None


def vite_entry(name: str) -> Markup:
    """Render the tags that load the Vite entry `name` (dev server or built bundle)."""
    dev_url = (current_app.config.get("VITE_DEV_SERVER_URL") or "").rstrip("/")

    if dev_url and name in ENTRIES:
        # The dev server serves everything below the build's `base`.
        return Markup(
            '<script type="module" src="{url}/static/dist/@vite/client"></script>\n'
            '<script type="module" src="{url}/static/dist/{src}"></script>'
        ).format(url=dev_url, src=ENTRIES[name])

    manifest = _load_manifest()
    chunk = _find_entry(manifest, name) if manifest else None

    if chunk is None:
        current_app.logger.warning("Vite entry '%s' is not built.", name)
        return Markup("<!-- vite entry '{}' not built -->").format(escape(name))

    imports = _collect_imports(manifest, chunk, set())
    css_files: List[str] = []
    for c in [chunk, *imports]:
        for css in c.get("css", []):
            if css not in css_files:
                css_files.append(css)

    tags = [
        Markup('<link rel="stylesheet" href="{}">').format(_asset_url(css))
        for css in css_files
    ]
    tags += [
        Markup('<link rel="modulepreload" href="{}">').format(_asset_url(c["file"]))
        for c in imports
    ]
    tags.append(
        Markup('<script type="module" src="{}"></script>').format(
            _asset_url(chunk["file"])
        )
    )
    return Markup("\n").join(tags)
