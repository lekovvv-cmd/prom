import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(prefix='shpiu_test_', suffix='.db')}"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-thirty-two-bytes"
os.environ["UPLOADS_DIR"] = tempfile.mkdtemp(prefix="shpiu_uploads_")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.modules.attachments import models as attachment_models  # noqa: F401
from app.modules.projects import models as project_models  # noqa: F401
from app.modules.responses import models as response_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401
from scripts.seed import main as seed_main


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.create_all(engine)
    seed_main()
    yield
    engine.dispose()
    db_path = os.environ["DATABASE_URL"].replace("sqlite:///", "")
    Path(db_path).unlink(missing_ok=True)
    shutil.rmtree(os.environ["UPLOADS_DIR"], ignore_errors=True)


@pytest.fixture()
def client(database):
    with TestClient(app) as test_client:
        yield test_client
