from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import AttachmentOwnerType, ProjectStatus, ProjectType, UserRole
from app.core.exceptions import DomainError
from app.core.schemas.common import PaginatedResponse
from app.modules.attachments.repository import AttachmentRepository
from app.modules.attachments.schemas import AttachmentRead
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import (
    ProjectCandidateRead,
    ProjectCompetencyBlock,
    ProjectCompetencyCoverage,
    ProjectCreate,
    ProjectDetails,
    ProjectMemberRead,
    ProjectRecommendationRead,
    ProjectSummary,
    ProjectUpdate,
)
from app.modules.users.repository import UserRepository
from app.modules.users.models import User
from app.modules.users.schemas import UserShort

UNSET = object()
DEFAULT_COMPETENCY_BLOCK_TITLE = "Общие компетенции"


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def list_public(
        self,
        *,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectSummary]:
        return self._list(
            public=True,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def list_admin(
        self,
        *,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
        current_user: User | None = None,
    ) -> PaginatedResponse[ProjectSummary]:
        return self._list(
            public=False,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            manager_user_id=self._manager_scope_user_id(current_user),
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def list_current_user_projects(
        self,
        *,
        current_user: User,
        search: str | None,
        status: ProjectStatus | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectSummary]:
        rows, total, safe_limit, safe_offset = self.repo.list_user_projects(
            user_id=current_user.id,
            email=current_user.email,
            search=search,
            status=status,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_summary(project, count) for project, count in rows],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    def list_recommendations(self, current_user: User, limit: int | None = None) -> list[ProjectRecommendationRead]:
        if current_user.role == UserRole.ADMIN:
            return []

        rows, _, _, _ = self.repo.list_projects(
            public=True,
            search=None,
            status=None,
            project_type=None,
            competency=None,
            manager_user_id=None,
            sort="created_at_desc",
            limit=100,
            offset=0,
        )
        responded_project_ids = self.repo.list_user_response_project_ids(current_user.id, current_user.email)
        user_project_ids = {
            project.id
            for project, _ in rows
            if any(member.user_id == current_user.id for member in project.members)
        }

        recommendations = [
            recommendation
            for project, responses_count in rows
            if project.id not in responded_project_ids and project.id not in user_project_ids
            for recommendation in [self._to_recommendation(project, responses_count, current_user)]
            if recommendation.score > 0
        ]
        recommendations.sort(key=lambda item: (-item.score, item.project.created_at), reverse=False)
        return recommendations[: min(max(limit or 5, 1), 10)]

    def get_public_details(self, project_id: UUID) -> ProjectDetails:
        project, count = self._get_existing_with_count(project_id)
        if (
            project.status in {ProjectStatus.DRAFT, ProjectStatus.ARCHIVED}
            or project.archived_at is not None
            or project.deleted_at is not None
        ):
            raise DomainError("Проект не найден", status_code=404)
        return self._to_details(project, count)

    def get_admin_details(self, project_id: UUID, current_user: User | None = None) -> ProjectDetails:
        self._ensure_can_manage_project(project_id, current_user)
        project, count = self._get_existing_with_count(project_id)
        return self._to_details(project, count)

    def get_current_user_project_details(self, project_id: UUID, current_user: User) -> ProjectDetails:
        project, count = self._get_existing_with_count(project_id)
        if not self.repo.user_can_view_project(project_id, current_user.id, current_user.email):
            raise DomainError("Недостаточно прав для просмотра этого проекта", status_code=403)
        return self._to_details(project, count)

    def get_existing_project(self, project_id: UUID) -> Project:
        project = self.repo.get_by_id(project_id)
        if project is None or project.deleted_at is not None:
            raise DomainError("Проект не найден", status_code=404)
        return project

    def create(self, payload: ProjectCreate, created_by: UUID) -> ProjectDetails:
        data = self._normalize_competency_data(payload.model_dump())
        member_ids = self._ensure_users_exist(data.pop("working_group_member_ids", []))
        self._ensure_responsible_exists(payload.responsible_user_id)
        project = self.repo.create(data=data, created_by=created_by)
        self.repo.replace_working_group(project, member_ids)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def update(self, project_id: UUID, payload: ProjectUpdate, current_user: User | None = None) -> ProjectDetails:
        self._ensure_can_manage_project(project_id, current_user)
        project = self.get_existing_project(project_id)
        data = self._normalize_competency_data(payload.model_dump(exclude_unset=True))
        member_ids = data.pop("working_group_member_ids", UNSET)
        self._ensure_responsible_exists(data.get("responsible_user_id"))
        if member_ids is not UNSET:
            normalized_member_ids = self._ensure_users_exist(member_ids or [])
            self.repo.replace_working_group(project, normalized_member_ids)
        self.repo.update(project, data)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def archive(self, project_id: UUID, current_user: User | None = None) -> None:
        self._ensure_can_manage_project(project_id, current_user)
        project = self.get_existing_project(project_id)
        if project.status == ProjectStatus.ARCHIVED or project.archived_at is not None:
            self.repo.soft_delete(project)
        else:
            self.repo.archive(project)
        self.db.commit()

    def restore(self, project_id: UUID, current_user: User | None = None) -> ProjectDetails:
        self._ensure_can_manage_project(project_id, current_user)
        project = self.get_existing_project(project_id)
        if project.status != ProjectStatus.ARCHIVED and project.archived_at is None:
            raise DomainError("Проект не находится в архиве")
        self.repo.restore_from_archive(project)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def list_candidates(
        self,
        *,
        project_id: UUID,
        current_user: User,
        search: str | None,
        block_title: str | None,
        competency: str | None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectCandidateRead]:
        self._ensure_can_manage_project(project_id, current_user)
        project, _ = self._get_existing_with_count(project_id)
        users = UserRepository(self.db).list_directory(search)
        response_user_ids = self.repo.list_project_response_user_ids(project_id)
        member_user_ids = {member.user_id for member in project.members}
        blocks = self._candidate_blocks(project, block_title)
        candidates = [
            self._to_candidate(user, blocks, response_user_ids, member_user_ids)
            for user in users
            if user.id != current_user.id or current_user.role == UserRole.ADMIN
        ]
        if competency:
            candidates = [
                candidate
                for candidate in candidates
                if self._candidate_matches_competency(candidate, competency)
            ]

        if sort == "name_asc":
            candidates.sort(key=lambda candidate: candidate.full_name.casefold())
        elif sort == "responses_asc":
            candidates.sort(key=lambda candidate: (candidate.has_response, -candidate.match_score, candidate.full_name))
        else:
            candidates.sort(key=lambda candidate: (-candidate.match_score, candidate.full_name.casefold()))

        safe_limit = min(max(limit or 100, 1), 200)
        safe_offset = max(offset or 0, 0)
        return PaginatedResponse(
            items=candidates[safe_offset : safe_offset + safe_limit],
            total=len(candidates),
            limit=safe_limit,
            offset=safe_offset,
        )

    def add_working_group_member(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        current_user: User,
    ) -> ProjectDetails:
        self._ensure_can_manage_project(project_id, current_user)
        project, _ = self._get_existing_with_count(project_id)
        user = UserRepository(self.db).get_by_id(user_id)
        if user is None or user.role == UserRole.ADMIN:
            raise DomainError("Сотрудник не найден", status_code=404)
        self.repo.add_working_group_member(project, user.id)
        self.db.commit()
        project, count = self._get_existing_with_count(project.id)
        return self._to_details(project, count)

    def _candidate_blocks(self, project: Project, block_title: str | None) -> list[ProjectCompetencyBlock]:
        blocks = self._project_competency_blocks(project)
        if not block_title:
            return blocks
        normalized_title = block_title.strip().casefold()
        return [block for block in blocks if block.title.casefold() == normalized_title]

    def _to_candidate(
        self,
        user: User,
        blocks: list[ProjectCompetencyBlock],
        response_user_ids: set[UUID],
        member_user_ids: set[UUID],
    ) -> ProjectCandidateRead:
        user_competencies = {
            competency.casefold(): competency
            for competency in self._split_competencies(user.competencies)
        }
        matched_competencies: list[str] = []
        matched_blocks: list[str] = []
        for block in blocks:
            block_has_match = False
            for competency in block.competencies:
                if competency.casefold() in user_competencies and competency not in matched_competencies:
                    matched_competencies.append(competency)
                    block_has_match = True
            if block_has_match:
                matched_blocks.append(block.title)

        return ProjectCandidateRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            position=user.position,
            competencies=user.competencies,
            about=user.about,
            matched_competencies=matched_competencies,
            matched_blocks=matched_blocks,
            match_score=len(matched_competencies),
            is_working_group_member=user.id in member_user_ids,
            has_response=user.id in response_user_ids,
        )

    def _candidate_matches_competency(self, candidate: ProjectCandidateRead, competency: str) -> bool:
        competency_query = competency.strip().casefold()
        candidate_competencies = self._split_competencies(candidate.competencies)
        return any(competency_query in item.casefold() for item in candidate_competencies) or any(
            competency_query in item.casefold() for item in candidate.matched_competencies
        )

    def _to_recommendation(
        self,
        project: Project,
        responses_count: int,
        user: User,
    ) -> ProjectRecommendationRead:
        user_competencies = {
            competency.casefold(): competency
            for competency in self._split_competencies(user.competencies)
        }
        matched_competencies: list[str] = []
        matched_blocks: list[str] = []
        score = 0
        for block in self._project_competency_blocks(project):
            block_matched = False
            for competency in block.competencies:
                if competency.casefold() in user_competencies and competency not in matched_competencies:
                    matched_competencies.append(competency)
                    score += 5
                    block_matched = True
            if block_matched:
                matched_blocks.append(block.title)
                score += 1

        matched_profile_terms: list[str] = []
        profile_terms = self._profile_terms(user)
        project_text = " ".join(
            value
            for value in (
                project.title,
                project.short_description,
                project.goal,
                project.required_competencies or "",
                " ".join(block.title for block in self._project_competency_blocks(project)),
            )
            if value
        ).casefold()
        for term in profile_terms:
            if term.casefold() in project_text and term not in matched_profile_terms:
                matched_profile_terms.append(term)
                score += 3 if term in self._split_competencies(user.about) else 1

        reasons: list[str] = []
        if matched_competencies:
            reasons.append("Совпадают компетенции из профиля")
        if matched_blocks:
            reasons.append("Совпадают направления работы")
        if matched_profile_terms:
            reasons.append("Есть совпадения с описанием профиля")

        return ProjectRecommendationRead(
            project=self._to_summary(project, responses_count),
            score=score,
            matched_competencies=matched_competencies,
            matched_blocks=matched_blocks,
            matched_profile_terms=matched_profile_terms[:5],
            reasons=reasons,
        )

    def _list(
        self,
        *,
        public: bool,
        search: str | None,
        status: ProjectStatus | None,
        project_type: ProjectType | None,
        competency: str | None,
        manager_user_id: UUID | None = None,
        sort: str,
        limit: int | None,
        offset: int | None,
    ) -> PaginatedResponse[ProjectSummary]:
        rows, total, safe_limit, safe_offset = self.repo.list_projects(
            public=public,
            search=search,
            status=status,
            project_type=project_type,
            competency=competency,
            manager_user_id=manager_user_id,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponse(
            items=[self._to_summary(project, count) for project, count in rows],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    @classmethod
    def _normalize_competency_data(cls, data: dict) -> dict:
        has_blocks = "competency_blocks" in data
        has_required = "required_competencies" in data
        if not has_blocks and not has_required:
            return data

        if has_blocks:
            blocks = cls._normalize_competency_blocks(
                data.get("competency_blocks"),
                data.get("required_competencies"),
            )
            data["competency_blocks"] = blocks
            data["required_competencies"] = cls._flatten_competency_blocks(blocks)
            return data

        required_competencies = cls._normalize_competencies_text(data.get("required_competencies"))
        data["required_competencies"] = required_competencies
        data["competency_blocks"] = cls._blocks_from_required_competencies(required_competencies)
        return data

    @classmethod
    def _normalize_competency_blocks(
        cls,
        blocks: list[dict] | None,
        fallback_required_competencies: str | None,
    ) -> list[dict]:
        normalized_blocks: list[dict] = []
        for block in blocks or []:
            title = str(block.get("title", "")).strip() or DEFAULT_COMPETENCY_BLOCK_TITLE
            competencies = cls._normalize_competency_items(block.get("competencies", []))
            if competencies:
                normalized_blocks.append({"title": title, "competencies": competencies})

        if normalized_blocks:
            return normalized_blocks

        return cls._blocks_from_required_competencies(
            cls._normalize_competencies_text(fallback_required_competencies)
        )

    @classmethod
    def _blocks_from_required_competencies(cls, required_competencies: str | None) -> list[dict]:
        competencies = cls._split_competencies(required_competencies)
        if not competencies:
            return []
        return [{"title": DEFAULT_COMPETENCY_BLOCK_TITLE, "competencies": competencies}]

    @classmethod
    def _flatten_competency_blocks(cls, blocks: list[dict]) -> str | None:
        return cls._join_competencies(
            competency
            for block in blocks
            for competency in cls._normalize_competency_items(block.get("competencies", []))
        )

    @classmethod
    def _normalize_competencies_text(cls, value: str | None) -> str | None:
        return cls._join_competencies(cls._split_competencies(value))

    @classmethod
    def _normalize_competency_items(cls, value: list[str] | str | None) -> list[str]:
        if isinstance(value, str):
            return cls._split_competencies(value)

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
    def _split_competencies(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.replace(";", ",").replace("\n", ",").split(",") if item.strip()]

    @staticmethod
    def _join_competencies(items) -> str | None:
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
    def _profile_terms(cls, user: User) -> list[str]:
        terms: list[str] = []
        terms.extend(cls._split_competencies(user.competencies))
        terms.extend(cls._split_competencies(user.about))
        for value in (user.department, user.position):
            if value:
                terms.extend(item.strip() for item in value.replace("/", ",").split(",") if item.strip())

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

    def _build_competency_coverage(self, project: Project) -> list[ProjectCompetencyCoverage]:
        accepted_counts: dict[str, int] = {}
        for response_competencies in self.repo.list_accepted_response_competencies(project.id):
            for competency in set(item.casefold() for item in self._split_competencies(response_competencies)):
                accepted_counts[competency] = accepted_counts.get(competency, 0) + 1

        coverage: list[ProjectCompetencyCoverage] = []
        for block in self._project_competency_blocks(project):
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
    def _manager_scope_user_id(current_user: User | None) -> UUID | None:
        if current_user is None or current_user.role == UserRole.ADMIN:
            return None
        return current_user.id

    def _ensure_can_manage_project(self, project_id: UUID, current_user: User | None) -> None:
        if current_user is None or current_user.role == UserRole.ADMIN:
            return
        if not self.repo.user_can_manage_project(project_id, current_user.id):
            raise DomainError("Недостаточно прав для управления этим проектом", status_code=403)

    def _get_existing_with_count(self, project_id: UUID) -> tuple[Project, int]:
        row = self.repo.get_with_counts(project_id)
        if row is None or row[0].deleted_at is not None:
            raise DomainError("Проект не найден", status_code=404)
        return row

    def _ensure_responsible_exists(self, responsible_user_id: UUID | None) -> None:
        if responsible_user_id is None:
            return
        if UserRepository(self.db).get_by_id(responsible_user_id) is None:
            raise DomainError("Ответственный не найден")

    def _ensure_users_exist(self, user_ids: list[UUID]) -> list[UUID]:
        repo = UserRepository(self.db)
        unique_user_ids: list[UUID] = []
        seen: set[UUID] = set()
        for user_id in user_ids:
            if user_id in seen:
                continue
            if repo.get_by_id(user_id) is None:
                raise DomainError("Участник рабочей группы не найден")
            seen.add(user_id)
            unique_user_ids.append(user_id)
        return unique_user_ids

    def _project_competency_blocks(self, project: Project) -> list[ProjectCompetencyBlock]:
        return [
            ProjectCompetencyBlock(**block)
            for block in self._normalize_competency_blocks(
                project.competency_blocks,
                project.required_competencies,
            )
        ]

    def _to_summary(self, project: Project, responses_count: int) -> ProjectSummary:
        return ProjectSummary(
            id=project.id,
            title=project.title,
            short_description=project.short_description,
            goal=project.goal,
            project_type=project.project_type,
            priority=project.priority,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            responsible=UserShort.model_validate(project.responsible) if project.responsible else None,
            required_competencies=project.required_competencies,
            competency_blocks=self._project_competency_blocks(project),
            responses_count=responses_count,
            created_at=project.created_at,
        )

    def _to_details(self, project: Project, responses_count: int) -> ProjectDetails:
        summary = self._to_summary(project, responses_count).model_dump()
        members = [
            ProjectMemberRead(
                id=member.user.id,
                full_name=member.user.full_name,
                email=member.user.email,
                member_role=member.member_role,
            )
            for member in project.members
        ]
        attachments = AttachmentRepository(self.db).list_for_owner(AttachmentOwnerType.PROJECT, project.id)
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
            competency_coverage=self._build_competency_coverage(project),
            planned_tasks=project.planned_tasks,
            updated_at=project.updated_at,
        )
