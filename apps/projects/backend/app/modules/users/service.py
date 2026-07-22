from uuid import UUID

from platform_sdk.auth import CurrentPrincipal
from platform_sdk.error_types import AuthenticationRequired, EntityNotFound
from platform_sdk.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy.orm import Session

from app.core.permissions import bind_principal, compatibility_role
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserProfileUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def sync_principal(self, principal: CurrentPrincipal) -> User:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            user = self._sync_principal(principal)
            uow.commit()
            return user

    def _sync_principal(self, principal: CurrentPrincipal) -> User:
        try:
            platform_user_id = UUID(principal.user_id)
        except ValueError as exc:
            raise AuthenticationRequired("Токен содержит некорректный идентификатор пользователя") from exc

        user = self.repo.get_by_id(platform_user_id)
        if user is None and principal.email:
            user = self.repo.get_by_email(principal.email.strip().lower())

        if user is None:
            if not principal.email:
                raise AuthenticationRequired(
                    "Токен нового пользователя должен содержать email для создания профильной проекции"
                )
            normalized_email = principal.email.strip().lower()
            user = self.repo.create(
                user_id=platform_user_id,
                email=normalized_email,
                full_name=principal.display_name or self._default_full_name(normalized_email),
                role=compatibility_role(principal),
            )
        else:
            if user.id != platform_user_id:
                raise AuthenticationRequired(
                    "Профиль с таким email уже связан с другим платформенным пользователем"
                )
            if principal.email:
                user.email = principal.email.strip().lower()
            if principal.display_name and not user.full_name.strip():
                user.full_name = principal.display_name.strip()
            user.role = compatibility_role(principal)

        self.db.flush()
        return bind_principal(user, principal)

    def get_by_id(self, user_id: object) -> User:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFound("Пользователь не найден")
        return user

    def list_all(self) -> list[User]:
        return self.repo.list_all()

    def list_directory(self, search: str | None = None) -> list[User]:
        return self.repo.list_directory(search)

    def update_profile(self, current_user: User, payload: UserProfileUpdate) -> User:
        with SqlAlchemyUnitOfWork(self.db) as uow:
            current_user.full_name = payload.full_name
            current_user.department = payload.department
            current_user.position = payload.position
            current_user.competencies = payload.competencies
            current_user.about = payload.about
            self.db.flush()
            self.db.refresh(current_user)
            uow.commit()
            return current_user

    @staticmethod
    def _default_full_name(email: str) -> str:
        if email == "admin@utmn.ru":
            return "Администратор ШПИУ"
        if email == "project.manager@utmn.ru":
            return "Руководитель проекта"
        if email == "sd.manager@utmn.ru":
            return "Менеджер Service Desk"
        if email == "sd.admin@utmn.ru":
            return "Администратор Service Desk"
        if email == "employee@utmn.ru":
            return "Сотрудник ШПИУ"
        return email.split("@", maxsplit=1)[0].replace(".", " ").title()
