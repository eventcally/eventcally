#!/usr/bin/env python3
"""Long-lived fixture server for the Playwright e2e suite.

The suite builds its fixtures by shelling out to the Flask CLI. Importing the app
costs ~3.8s, the actual database work is ~0.1s, and a full run makes ~464 such
calls -- roughly 37 of its ~40 minutes. This boots the app once and serves those
same commands over HTTP, which takes the full suite from ~30 minutes to ~3.5.

Commands are dispatched through the app's own CLI runner, so the fixture logic is
exactly the code `flask` would run; nothing is reimplemented here.

HTTP rather than stdin/stdout because Node exposes no file descriptor for a child
process's pipes (`child.stdout.fd` is undefined), so a reply cannot be read
synchronously -- and the fixtures must stay synchronous, or every `create*` call
site across the specs has to grow an `await`. `curl` is synchronously callable
from Node, so HTTP keeps the fixture API unchanged.

    POST /         {"args": ["test", "reset", "--seed"]}
                -> {"ok": true, "output": "Reset done.\n", "ms": 41}
    GET  /health -> {"ok": true, "database": "<fingerprint>"}

Run with the same environment the app needs (DATABASE_URL, SERVER_NAME, ...).
"""

import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Run as a script from .scripts/, so sys.path[0] is that directory, not the repo.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

os.environ.setdefault("TESTING", "1")

from project import create_app  # noqa: E402
from project.extensions import db  # noqa: E402


def database_fingerprint():
    """Identify the database without exposing the credentials in it.

    Every fixture command truncates the whole database, so a client must be able
    to prove it is talking to the server it meant to.
    """
    return hashlib.sha256(os.environ.get("DATABASE_URL", "").encode()).hexdigest()[:12]


app = create_app()
# mix_stderr=False is required, not cosmetic: click's runner otherwise folds
# stderr into `result.output`, so a SQLAlchemy warning ends up inside the JSON the
# fixtures parse. A real `flask` subprocess kept warnings on stderr.
runner = app.test_cli_runner(mix_stderr=False)


def run_command(args):
    started = time.monotonic()
    result = runner.invoke(args=args)
    elapsed = int((time.monotonic() - started) * 1000)

    # Each `flask` invocation got a fresh session; keep that true here, or the
    # identity map outlives a `reset` that truncated the rows behind it.
    with app.app_context():
        db.session.remove()

    if result.exit_code != 0:
        error = str(result.exception) if result.exception else result.stderr
        return {
            "ok": False,
            "exit_code": result.exit_code,
            "output": result.stdout,
            "error": error,
            "ms": elapsed,
        }

    return {"ok": True, "output": result.stdout, "ms": elapsed}


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"ok": True, "database": database_fingerprint()})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))

        try:
            args = json.loads(self.rfile.read(length))["args"]
        except Exception as e:
            return self._send({"ok": False, "error": f"bad request: {e}"}, 400)

        try:
            self._send(run_command(args))
        except Exception as e:
            self._send({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, *args):
        pass  # the suite's own output is the interesting one


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5099)
    port = parser.parse_args().port

    # Serial by design: the suite runs with workers: 1, because every reset
    # truncates the whole database.
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
