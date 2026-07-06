import type { User } from "../../user/model/types";

export type ProjectStatus = "draft" | "active" | "paused" | "completed" | "archived";
export type ProjectType = "strategic";
export type ProjectPriority = "low" | "medium" | "high" | "critical";

export type Attachment = {
  id: string;
  owner_type: "project" | "response" | "task";
  owner_id: string;
  file_name: string;
  content_type: string | null;
  size_bytes: number;
  download_url: string;
  created_at: string;
};

export type ProjectMember = Pick<User, "id" | "full_name" | "email"> & {
  member_role: "manager" | "working_group_member" | "participant";
};

export type ProjectCompetencyBlock = {
  title: string;
  competencies: string[];
};

export type ProjectCompetencyCoverage = {
  block_title: string;
  competency: string;
  accepted_count: number;
  is_covered: boolean;
  priority: "open" | "covered";
};

export type ProjectCandidate = Pick<User, "id" | "email" | "full_name" | "role" | "department" | "position"> & {
  competencies: string | null;
  about: string | null;
  matched_competencies: string[];
  matched_blocks: string[];
  match_score: number;
  is_working_group_member: boolean;
  has_response: boolean;
};

export type Project = {
  id: string;
  title: string;
  short_description: string;
  goal: string;
  project_type: ProjectType;
  priority: ProjectPriority;
  status: ProjectStatus;
  start_date: string | null;
  end_date: string | null;
  responsible: Pick<User, "id" | "full_name" | "email"> | null;
  required_competencies: string | null;
  competency_blocks: ProjectCompetencyBlock[];
  responses_count: number;
  created_at: string;
};

export type ProjectRecommendation = {
  project: Project;
  score: number;
  matched_competencies: string[];
  matched_blocks: string[];
  matched_profile_terms: string[];
  reasons: string[];
};

export type ProjectDetails = Project & {
  description: string;
  expected_result: string | null;
  contact_email: string | null;
  members: ProjectMember[];
  attachments: Attachment[];
  required_competencies: string | null;
  competency_coverage: ProjectCompetencyCoverage[];
  planned_tasks: string | null;
  updated_at: string;
};

export type ProjectListParams = {
  search?: string;
  status?: ProjectStatus | "";
  project_type?: ProjectType | "";
  competency?: string;
  sort?: "created_at_desc" | "created_at_asc" | "priority_desc" | "priority_asc";
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

export type ProjectMutationPayload = {
  title: string;
  short_description: string;
  description: string;
  goal: string;
  expected_result?: string | null;
  project_type: ProjectType;
  priority: ProjectPriority;
  status: ProjectStatus;
  start_date?: string | null;
  end_date?: string | null;
  responsible_user_id?: string | null;
  working_group_member_ids?: string[];
  contact_email?: string | null;
  required_competencies?: string | null;
  competency_blocks?: ProjectCompetencyBlock[];
  planned_tasks?: string | null;
};
