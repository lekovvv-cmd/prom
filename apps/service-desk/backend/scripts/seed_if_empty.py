"""Apply the demo catalog only on an empty Service Desk database."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.catalog.models import ServiceDeskService
from scripts.seed import main as seed


def main() -> None:
    with SessionLocal() as db:
        has_catalog = db.scalar(select(ServiceDeskService.id).limit(1)) is not None
    if has_catalog:
        print("Service Desk demo catalog exists; preserving current data")
    else:
        seed()


if __name__ == "__main__":
    main()
