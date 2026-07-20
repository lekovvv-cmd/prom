from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from access_service.infrastructure.database import engine


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = Config(root / "alembic.ini")
    config.set_main_option("script_location", str(root / "alembic"))
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "platform_users" in tables and "alembic_version" not in tables:
        columns = {column["name"] for column in inspector.get_columns("platform_users")}
        if "session_version" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE platform_users "
                        "ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1"
                    )
                )
        command.stamp(config, "202607160001")
    command.upgrade(config, "head")
    print("Access Service migrations are current")


if __name__ == "__main__":
    main()
