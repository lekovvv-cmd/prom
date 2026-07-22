from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from platform_sdk.error_types import EntityNotFound, InvalidRequest, PermissionDenied
from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType
from app.core.permissions import can_manage_all_projects, can_manage_own_projects
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.platform.events import ProjectEventRecorder
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import (
    ProjectCompetencyBlock,
    ProjectCompetencyCoverage,
    ProjectDetails,
    ProjectMemberRead,
    ProjectSummary,
)
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserShort


UNSET = object()
DEFAULT_COMPETENCY_BLOCK_TITLE = "Общие компетенции"


class ProjectServiceBase:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)
        self.events = ProjectEventRecorder(db)

    def get_existing_project(self, project_id: UUID) -> Project:
        project = self.repo.get_by_id(project_id)
        if project is None or project.deleted_at is not None:
            raise EntityNotFound("Проект не найден")
        return project

    @classmethod
    def normalize_competency_data(cls, data: dict) -> dict:
        has_blocks = "competency_blocks" in data
        has_required = "required_competencies" in data
        if not has_blocks and not has_required:
            return data
        if has_blocks:
            blocks = cls.normalize_competency_blocks(
                data.get("competency_blocks"),
                data.get("required_competencies"),
            )
            data["competency_blocks"] = blocks
            data["required_competencies"] = cls.flatten_competency_blocks(blocks)
            return data
        required = cls.normalize_competencies_text(data.get("required_competencies"))
        data["required_competencies"] = required
        data["competency_blocks"] = cls.blocks_from_required_competencies(required)
        return data

    @classmethod
    def normalize_competency_blocks(
        cls,
        blocks: list[dict] | None,
        fallback_required_competencies: str | None,
    ) -> list[dict]:
        normalized_blocks: list[dict] = []
        for block in blocks or []:
            title = str(block.get("title", "")).strip() or DEFAULT_COMPETENCY_BLOCK_TITLE
            competencies = cls.normalize_competency_items(block.get("competencies", []))
            if competencies:
                normalized_blocks.append({"title": title, "competencies": competencies})
        if normalized_blocks:
            return normalized_blocks
        return cls.blocks_from_required_competencies(
            cls.normalize_competencies_text(fallback_required_competencies)
        )

    @classmethod
    def blocks_from_required_competencies(
        cls,
        required_competencies: str | None,
    ) -> list[dict]:
        competencies = cls.split_competencies(required_competencies)
        if not competencies:
            return []
        return [{"title": DEFAULT_COMPETENCY_BLOCK_TITLE, "competencies": competencies}]

    @classmethod
    def flatten_competency_blocks(cls, blocks: list[dict]) -> str | None:
        return cls.join_competencies(
            competency
            for block in blocks
            for competency in cls.normalize_competency_items(block.get("competencies", []))
        )

    @classmethod
    def normalize_competencies_text(cls, value: str | None) -> str | None:
        return cls.join_competencies(cls.split_competencies(value))

    @classmethod
    def normalize_competency_items(cls, value: list[str] | str | None) -> list[str]:
        if isinstance(value, str):
            return cls.split_competencies(value)
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value or []:
            competency = str(item).strip()
            key = competency.casefold()
            if not competency or key in seen:
                continue
            seen.add(key)
            normalized.append(competency)
        return normalized

    @staticmethod
    def split_competencies(value: str | None) -> list[str]:
        if not value:
            return []
        return [
            item.strip()
            for item in value.replace(";", ",").replace("\n", ",").split(",")
            if item.strip()
        ]

    @staticmethod
    def join_competencies(items: Iterable[object]) -> str | None:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in items:
            competency = str(item).strip()
            key = competency.casefold()
            if not competency or key in seen:
                continue
            seen.add(key)
            normalized.append(competency)
        return ", ".join(normalized) if normalized else None

    @classmethod
    def profile_terms(cls, user: User) -> list[str]:
        terms = [
            *cls.split_competencies(user.competencies),
            *cls.split_competencies(user.about),
        ]
        for value in (user.department, user.position):
            if value:
                terms.extend(
                    item.strip() for item in value.replace("/", ",").split(",") if item.strip()
                )
        normalized: list[str] = []
        seen: set[str] = set()
        for term in terms:
            clean = term.strip()
            key = clean.casefold()
            if len(clean) < 3 or key in seen:
                continue
            seen.add(key)
            normalized.append(clean)
        return normalized[:20]

    def build_competency_coverage(self, project: Project) -> list[ProjectCompetencyCoverage]:
        accepted_counts: dict[str, int] = {}
        for response_competencies in self.repo.list_accepted_response_competencies(project.id):
            for competency in {
                item.casefold() for item in self.split_competencies(response_competencies)
            }:
                accepted_counts[competency] = accepted_counts.get(competency, 0) + 1
        coverage: list[ProjectCompetencyCoverage] = []
        for block in self.project_competency_blocks(project):
            for competency in block.competencies:
                accepted_count = accepted_counts.get(competency.casefold(), 0)
                coverage.append(
                    ProjectCompetencyCoverage(
                        block_title=block.title,
                        competency=competency,
                        accepted_count=accepted_count,
                        is_covered=accepted_count > 0,
                        priority="covered" if accepted_count > 0 else "open",
                    )
                )
        return coverage

    @staticmethod
    def manager_scope_user_id(current_user: User | None) -> UUID | None:
        if current_user is None or can_manage_all_projects(current_user):
            return None
        return current_user.id

    def ensure_can_manage_project(
        self,
        project_id: UUID,
        current_user: User | None,
    ) -> None:
        if current_user is None or can_manage_all_projects(current_user):
            return
        if not can_manage_own_projects(current_user) or not self.repo.user_can_manage_project(
            project_id,
            current_user.id,
        ):
            raise PermissionDenied("Недостаточно прав для управления этим проектом")

    def get_existing_with_count(self, project_id: UUID) -> tuple[Project, int]:
        row = self.repo.get_with_counts(project_id)
        if row is None or row[0].deleted_at is not None:
            raise EntityNotFound("Проект не найден")
        return row

    def ensure_responsible_exists(self, responsible_user_id: UUID | None) -> None:
        if responsible_user_id is None:
            return
        if UserRepository(self.db).get_by_id(responsible_user_id) is None:
            raise InvalidRequest("Ответственный не найден")

    def ensure_users_exist(self, user_ids: list[UUID]) -> list[UUID]:
        repo = UserRepository(self.db)
        unique_user_ids: list[UUID] = []
        seen: set[UUID] = set()
        for user_id in user_ids:
            if user_id in seen:
                continue
            if repo.get_by_id(user_id) is None:
                raise InvalidRequest("Участник рабочей группы не найден")
            seen.add(user_id)
            unique_user_ids.append(user_id)
        return unique_user_ids

    def project_competency_blocks(self, project: Project) -> list[ProjectCompetencyBlock]:
        return [
            ProjectCompetencyBlock(**block)
            for block in self.normalize_competency_blocks(
                project.competency_blocks,
                project.required_competencies,
            )
        ]

    def to_summary(self, project: Project, responses_count: int) -> ProjectSummary:
        return ProjectSummary(
            id=project.id,
            version=project.version,
            title=project.title,
            short_description=project.short_description,
            goal=project.goal,
            project_type=project.project_type,
            priority=project.priority,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            responsible=(
                UserShort.model_validate(project.responsible) if project.responsible else None
            ),
            required_competencies=project.required_competencies,
            competency_blocks=self.project_competency_blocks(project),
            responses_count=responses_count,
            created_at=project.created_at,
        )

    def to_details(self, project: Project, responses_count: int) -> ProjectDetails:
        summary = self.to_summary(project, responses_count).model_dump()
        members = [
            ProjectMemberRead(
                id=member.user.id,
                full_name=member.user.full_name,
                email=member.user.email,
                member_role=member.member_role,
            )
            for member in project.members
        ]
        attachments = AttachmentRepository(self.db).list_for_owner(
            AttachmentOwnerType.PROJECT,
            project.id,
        )
        return ProjectDetails(
            **summary,
            description=project.description,
            expected_result=project.expected_result,
            contact_email=project.contact_email,
            members=members,
            attachments=[
                AttachmentRead(
                    id=attachment.id,
                    owner_type=attachment.owner_type,
                    owner_id=attachment.owner_id,
                    file_name=attachment.file_name,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    download_url=f"/api/attachments/{attachment.id}",
                    created_at=attachment.created_at,
                )
                for attachment in attachments
            ],
            competency_coverage=self.build_competency_coverage(project),
            planned_tasks=project.planned_tasks,
            updated_at=project.updated_at,
        )
