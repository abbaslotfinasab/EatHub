"""Isolated SQLite settings for focused backend test-runner processes.

The verified filesystem copy is the configured base database. Django's test
runner uses a distinct, unique file under the process temp root and owns that
test database's creation and removal.
"""

from pathlib import Path as _Path
from tempfile import gettempdir as _gettempdir
from uuid import uuid4 as _uuid4

from django.core.exceptions import ImproperlyConfigured as _ImproperlyConfigured

from EatHub.settings import *  # noqa: F403


_REPOSITORY_ROOT = _Path(BASE_DIR).resolve().parent
_DEVELOPMENT_DATABASE = _Path(BASE_DIR) / "db.sqlite3"
_BASE_DATABASE = _Path(
    r"C:\Users\abbas\AppData\Local\Temp\eathub-development-copy-0a98704f0a984c44a21dc4e70b29639d.sqlite3"
).absolute()
_TEST_DATABASE_DIRECTORY = _Path(_gettempdir()).absolute()

if _BASE_DATABASE == _DEVELOPMENT_DATABASE or not _BASE_DATABASE.is_file():
    raise _ImproperlyConfigured(
        "The isolated test base database copy is missing or resolves to the development database."
    )

try:
    _TEST_DATABASE_DIRECTORY.relative_to(_REPOSITORY_ROOT)
except ValueError:
    pass
else:
    raise _ImproperlyConfigured(
        "The disposable test database directory must be outside the repository."
    )

while True:
    _TEST_DATABASE = _TEST_DATABASE_DIRECTORY / f"eathub-test-{_uuid4().hex}.sqlite3"
    if (
        _TEST_DATABASE != _BASE_DATABASE
        and _TEST_DATABASE != _DEVELOPMENT_DATABASE
        and not _TEST_DATABASE.exists()
    ):
        break

if _TEST_DATABASE.parent != _TEST_DATABASE_DIRECTORY:
    raise _ImproperlyConfigured(
        "The disposable test database path failed its isolation checks."
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(_BASE_DATABASE),
        "TEST": {"NAME": str(_TEST_DATABASE)},
    }
}

DATABASE_ROUTERS = []
