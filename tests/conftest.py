import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from starlette.testclient import TestClient


_sqlite_path: str | None = None


def pytest_configure() -> None:
    global _sqlite_path
    fd, _sqlite_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    abs_path = Path(_sqlite_path).resolve().as_posix()
    os.environ["DATABASE_URL"] = f"sqlite:///{abs_path}"
    os.environ.setdefault("SECRET_KEY", "test-secret-key-exactly-32-bytes!!")


def pytest_unconfigure() -> None:
    global _sqlite_path
    if _sqlite_path and Path(_sqlite_path).is_file():
        try:
            Path(_sqlite_path).unlink()
        except OSError:
            pass
    _sqlite_path = None


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from src.serving.app import app

    with TestClient(app) as c:
        yield c
