from __future__ import annotations

from uuid import UUID

from app.core.permissions import is_platform_admin
from app.core.schemas.common import PaginatedResponse
from app.modules.projects.models import Project
from app.modules.projects.schemas import (
    ProjectCandidateRead,
    ProjectCompetencyBlock,
    ProjectRecommendationRead,
)
from app.modules.projects.service_base import ProjectServiceBase
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class ProjectRecommendationService(ProjectServiceBase):
    def list_recommendations(
        self,
        current_user: User,
        limit: int | None = None,
    ) -> list[ProjectRecommendationRead]:
        if is_platform_admin(current_user):
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
        responded_project_ids = self.repo.list_user_response_project_ids(
            current_user.id,
            current_user.email,
        )
        user_project_ids = {
            project.id
            for project, _ in rows
            if any(member.user_id == current_user.id for member in project.members)
        }
        recommendations = [
            recommendation
            for project, responses_count in rows
            if project.id not in responded_project_ids and project.id not in user_project_ids
            for recommendation in [
                self._to_recommendation(project, responses_count, current_user)
            ]
            if recommendation.score > 0
        ]
        recommendations.sort(key=lambda item: (-item.score, item.project.created_at))
        return recommendations[: min(max(limit or 5, 1), 10)]

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
        self.ensure_can_manage_project(project_id, current_user)
        project, _ = self.get_existing_with_count(project_id)
        users = UserRepository(self.db).list_directory(search)
        response_user_ids = self.repo.list_project_response_user_ids(project_id)
        member_user_ids = {member.user_id for member in project.members}
        blocks = self._candidate_blocks(project, block_title)
        candidates = [
            self._to_candidate(user, blocks, response_user_ids, member_user_ids)
            for user in users
            if user.id != current_user.id or is_platform_admin(current_user)
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
            candidates.sort(
                key=lambda candidate: (
                    candidate.has_response,
                    -candidate.match_score,
                    candidate.full_name,
                )
            )
        else:
            candidates.sort(
                key=lambda candidate: (
                    -candidate.match_score,
                    candidate.full_name.casefold(),
                )
            )
        safe_limit = min(max(limit or 100, 1), 200)
        safe_offset = max(offset or 0, 0)
        return PaginatedResponse(
            items=candidates[safe_offset : safe_offset + safe_limit],
            total=len(candidates),
            limit=safe_limit,
            offset=safe_offset,
        )

    def _candidate_blocks(
        self,
        project: Project,
        block_title: str | None,
    ) -> list[ProjectCompetencyBlock]:
        blocks = self.project_competency_blocks(project)
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
            for competency in self.split_competencies(user.competencies)
        }
        matched_competencies: list[str] = []
        matched_blocks: list[str] = []
        for block in blocks:
            block_has_match = False
            for competency in block.competencies:
                if (
                    competency.casefold() in user_competencies
                    and competency not in matched_competencies
                ):
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

    def _candidate_matches_competency(
        self,
        candidate: ProjectCandidateRead,
        competency: str,
    ) -> bool:
        competency_query = competency.strip().casefold()
        candidate_competencies = self.split_competencies(candidate.competencies)
        return any(
            competency_query in item.casefold() for item in candidate_competencies
        ) or any(
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
            for competency in self.split_competencies(user.competencies)
        }
        matched_competencies: list[str] = []
        matched_blocks: list[str] = []
        score = 0
        for block in self.project_competency_blocks(project):
            block_matched = False
            for competency in block.competencies:
                if (
                    competency.casefold() in user_competencies
                    and competency not in matched_competencies
                ):
                    matched_competencies.append(competency)
                    score += 5
                    block_matched = True
            if block_matched:
                matched_blocks.append(block.title)
                score += 1
        matched_profile_terms: list[str] = []
        project_text = " ".join(
            value
            for value in (
                project.title,
                project.short_description,
                project.goal,
                project.required_competencies or "",
                " ".join(block.title for block in self.project_competency_blocks(project)),
            )
            if value
        ).casefold()
        for term in self.profile_terms(user):
            if term.casefold() in project_text and term not in matched_profile_terms:
                matched_profile_terms.append(term)
                score += 3 if term in self.split_competencies(user.about) else 1
        reasons: list[str] = []
        if matched_competencies:
            reasons.append("Совпадают компетенции из профиля")
        if matched_blocks:
            reasons.append("Совпадают направления работы")
        if matched_profile_terms:
            reasons.append("Есть совпадения с описанием профиля")
        return ProjectRecommendationRead(
            project=self.to_summary(project, responses_count),
            score=score,
            matched_competencies=matched_competencies,
            matched_blocks=matched_blocks,
            matched_profile_terms=matched_profile_terms[:5],
            reasons=reasons,
        )
