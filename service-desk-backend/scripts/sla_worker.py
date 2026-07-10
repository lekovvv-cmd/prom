from app.core.database import SessionLocal
from app.modules.sla.worker import SlaWorker


def main() -> None:
    with SessionLocal() as db:
        print(SlaWorker(db).run_once())


if __name__ == "__main__":
    main()
