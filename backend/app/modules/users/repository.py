from sqlalchemy import or_, select
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

    def list_directory(self, search: str | None = None) -> list[User]:
        query = select(User).where(User.role != UserRole.ADMIN)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    User.department.ilike(pattern),
                    User.position.ilike(pattern),
                    User.competencies.ilike(pattern),
                )
            )
        return list(self.db.scalars(query.order_by(User.full_name.asc(), User.email.asc())))

    def create(
        self,
        *,
        email: str,
        full_name: str,
        role: UserRole = UserRole.EMPLOYEE,
        department: str | None = None,
        position: str | None = None,
        competencies: str | None = None,
        about: str | None = None,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            department=department,
            position=position,
            competencies=competencies,
            about=about,
        )
        self.db.add(user)
        self.db.flush()
        return user
