# ruff: noqa: E402

import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

TEST_DATABASE_URL = os.getenv("PROJECTS_TEST_DATABASE_URL")
os.environ["PROJECTS_DATABASE_URL"] = TEST_DATABASE_URL or (
    f"sqlite:///{tempfile.mktemp(prefix='shpiu_test_', suffix='.db')}"
)
os.environ["PROJECTS_JWT_SECRET"] = "test-secret-with-at-least-thirty-two-bytes"
os.environ["PROJECTS_ALLOW_LEGACY_TOKENS"] = "true"
os.environ["PROJECTS_UPLOADS_DIR"] = tempfile.mkdtemp(prefix="shpiu_uploads_")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.modules.attachments import models as attachment_models  # noqa: F401
from app.modules.platform import models as platform_models  # noqa: F401
from app.modules.projects import models as project_models  # noqa: F401
from app.modules.reports import models as report_models  # noqa: F401
from app.modules.responses import models as response_models  # noqa: F401
from app.modules.tasks import models as task_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401
from scripts.seed import main as seed_main


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.create_all(engine)
    seed_main()
    yield
    engine.dispose()
    if os.environ["PROJECTS_DATABASE_URL"].startswith("sqlite:///"):
        db_path = os.environ["PROJECTS_DATABASE_URL"].replace("sqlite:///", "")
        Path(db_path).unlink(missing_ok=True)
    shutil.rmtree(os.environ["PROJECTS_UPLOADS_DIR"], ignore_errors=True)


@pytest.fixture()
def client(database):
    with TestClient(app) as test_client:
        yield test_client
