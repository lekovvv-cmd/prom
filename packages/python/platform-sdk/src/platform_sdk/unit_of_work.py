from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass(slots=True)
class SqlAlchemyUnitOfWork:
    """Small explicit transaction boundary for one application use case."""

    session: Session
    committed: bool = False

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()
        self.committed = True

    def rollback(self) -> None:
        self.session.rollback()
        self.committed = False

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        if exc_type is not None or not self.committed:
            self.rollback()
