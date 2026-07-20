from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork


def test_unit_of_work_rolls_back_when_not_committed() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as session:
        with SqlAlchemyUnitOfWork(session):
            session.execute(text("CREATE TABLE sample (value INTEGER)"))
            session.execute(text("INSERT INTO sample VALUES (1)"))
        assert session.scalar(text("SELECT count(*) FROM sample")) == 0


def test_unit_of_work_commits_explicitly() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as session:
        session.execute(text("CREATE TABLE sample (value INTEGER)"))
        session.commit()
        with SqlAlchemyUnitOfWork(session) as unit_of_work:
            session.execute(text("INSERT INTO sample VALUES (1)"))
            unit_of_work.commit()
        assert session.scalar(text("SELECT count(*) FROM sample")) == 1
