from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: object) -> User | None:
        return self.db.get(User, user_id)

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.full_name.asc(), User.email.asc())))

    def create(
        self,
        *,
        email: str,
        full_name: str,
        role: UserRole = UserRole.EMPLOYEE,
        department: str | None = None,
        position: str | None = None,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            department=department,
            position=position,
        )
        self.db.add(user)
        self.db.flush()
        return user
