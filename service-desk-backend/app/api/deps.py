from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_session


def get_db() -> Generator[Session]:
    yield from get_session()
