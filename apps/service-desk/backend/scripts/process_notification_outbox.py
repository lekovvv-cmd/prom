from app.core.database import SessionLocal
from app.modules.notifications.worker import NotificationOutboxWorker


def main() -> None:
    with SessionLocal() as db:
        print(NotificationOutboxWorker(db).run_once())


if __name__ == "__main__":
    main()
