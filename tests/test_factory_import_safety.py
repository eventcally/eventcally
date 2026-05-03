import os
import subprocess
import sys


def test_models_import_without_database_url_or_app_creation():
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)
    env.pop("TEST_DATABASE_URL", None)

    code = """
import project
from project.models import Event, User, AdminUnit

assert Event is not None
assert User is not None
assert AdminUnit is not None
assert not hasattr(project, 'app')
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Import should work without DATABASE_URL or app creation. "
        f"stderr={result.stderr} stdout={result.stdout}"
    )
