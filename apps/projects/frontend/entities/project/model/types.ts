import type { components as ProjectsContract } from "@prom/generated-contracts/projects";

type Schemas = ProjectsContract["schemas"];

export type ProjectStatus = Schemas["ProjectStatus"];
type ProjectType = Schemas["ProjectType"];
export type ProjectPriority = Schemas["ProjectPriority"];
export type Attachment = Schemas["AttachmentRead"];
export type ProjectMember = Schemas["ProjectMemberRead"];
export type ProjectCompetencyBlock = Omit<
  Schemas["ProjectCompetencyBlock"],
  "competencies"
> & {
  competencies: string[];
};
export type ProjectCompetencyCoverage = Schemas["ProjectCompetencyCoverage"];
export type ProjectCandidate = Omit<
  Schemas["ProjectCandidateRead"],
  "matched_blocks" | "matched_competencies"
> & {
  matched_blocks: string[];
  matched_competencies: string[];
};
export type Project = Omit<Schemas["ProjectSummary"], "competency_blocks"> & {
  competency_blocks: ProjectCompetencyBlock[];
};
export type ProjectRecommendation = Omit<
  Schemas["ProjectRecommendationRead"],
  | "matched_blocks"
  | "matched_competencies"
  | "matched_profile_terms"
  | "project"
  | "reasons"
> & {
  matched_blocks: string[];
  matched_competencies: string[];
  matched_profile_terms: string[];
  project: Project;
  reasons: string[];
};
export type ProjectDetails = Omit<
  Schemas["ProjectDetails"],
  "competency_blocks" | "competency_coverage"
> & {
  competency_blocks: ProjectCompetencyBlock[];
  competency_coverage: ProjectCompetencyCoverage[];
};

export type ProjectListParams = {
  search?: string;
  status?: ProjectStatus | "";
  project_type?: ProjectType | "";
  competency?: string;
  sort?:
    "created_at_desc" | "created_at_asc" | "priority_desc" | "priority_asc";
  limit?: number;
  offset?: number;
};

export type ProjectCandidateParams = {
  search?: string;
  block_title?: string;
  competency?: string;
  sort?: "match_desc" | "name_asc" | "responses_asc";
  limit?: number;
  offset?: number;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type ProjectMutationPayload = Omit<
  Schemas["ProjectCreate"],
  "competency_blocks"
> & {
  competency_blocks?: ProjectCompetencyBlock[];
};
