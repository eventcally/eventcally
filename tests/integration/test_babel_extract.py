import os
import subprocess
import sys


def test_babel_extract_runs_without_app_context_or_database_url():
    """`pybabel` runs as a bare CLI: no Flask app, no environment, no database.

    The extractor used to reach for `flask.current_app`, which made
    `.scripts/translations/extract.sh` fail with "Working outside of application
    context" and left the catalogs empty.
    """
    env = os.environ.copy()
    for key in ("DATABASE_URL", "TEST_DATABASE_URL", "REDIS_URL", "SERVER_NAME"):
        env.pop(key, None)

    code = """
from project.babel import babel_extract

messages = babel_extract(None, [], [], {})

assert messages, "extractor returned no messages"

lineno, funcname, message, comments = messages[0]
assert lineno == 1
assert funcname == ""
assert isinstance(message, str)
assert isinstance(comments, list)

extracted = {entry[2] for entry in messages}
for expected in ("Event", "Events", "Webhook", "Webhooks"):
    assert expected in extracted, f"{expected} missing from {sorted(extracted)}"

# Review statuses are localized from the enum member at runtime, so every
# member has to be extracted here -- including the ones no form offers.
for expected in (
    "EventReferenceRequestReviewStatus.inbox",
    "EventReferenceRequestReviewStatus.verified",
    "EventReferenceRequestReviewStatus.rejected",
    "AdminUnitVerificationRequestReviewStatus.inbox",
    "AdminUnitVerificationRequestReviewStatus.verified",
    "AdminUnitVerificationRequestReviewStatus.rejected",
):
    assert expected in extracted, f"{expected} missing from {sorted(extracted)}"
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Extraction should work without an app context or DATABASE_URL. "
        f"stderr={result.stderr} stdout={result.stdout}"
    )
