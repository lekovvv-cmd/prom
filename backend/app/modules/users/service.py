from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import DomainError
from app.core.security import create_access_token, ensure_utmn_email
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserProfileUpdate

DEV_CODE = "000000"


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def request_code(self, email: str) -> dict[str, str]:
        normalized = ensure_utmn_email(email)
        return {
            "email": normalized,
            "dev_code": DEV_CODE,
            "message": "Для MVP используйте dev-код 000000",
        }

    def verify_code(self, email: str, code: str) -> tuple[User, str]:
        normalized = ensure_utmn_email(email)
        if code != DEV_CODE:
            raise DomainError("Неверный код подтверждения")

        user = self.repo.get_by_email(normalized)
        if user is None:
            user = self.repo.create(
                email=normalized,
                full_name=self._default_full_name(normalized),
                role=self._role_for_email(normalized),
            )
        else:
            expected_role = self._role_for_email(normalized)
            if user.role != expected_role and normalized in {"admin@utmn.ru", "manager@utmn.ru"}:
                user.role = expected_role

        self.db.commit()
        self.db.refresh(user)
        token = create_access_token(str(user.id))
        return user, token

    def get_by_id(self, user_id: object) -> User:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise DomainError("Пользователь не найден", status_code=404)
        return user

    def list_all(self) -> list[User]:
        return self.repo.list_all()

    def list_directory(self, search: str | None = None) -> list[User]:
        return self.repo.list_directory(search)

    def update_profile(self, current_user: User, payload: UserProfileUpdate) -> User:
        current_user.full_name = payload.full_name
        current_user.department = payload.department
        current_user.position = payload.position
        current_user.competencies = payload.competencies
        current_user.about = payload.about
        self.db.commit()
        self.db.refresh(current_user)
        return current_user

    @staticmethod
    def _role_for_email(email: str) -> UserRole:
        if email == "admin@utmn.ru":
            return UserRole.ADMIN
        if email == "manager@utmn.ru":
            return UserRole.PROJECT_MANAGER
        return UserRole.EMPLOYEE

    @staticmethod
    def _default_full_name(email: str) -> str:
        if email == "admin@utmn.ru":
            return "Администратор ШПИУ"
        if email == "manager@utmn.ru":
            return "Руководитель проекта"
        if email == "employee@utmn.ru":
            return "Сотрудник ШПИУ"
        return email.split("@", maxsplit=1)[0].replace(".", " ").title()
