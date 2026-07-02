export type ResponsesByProject = {
  project_id: string;
  project_title: string;
  responses_count: number;
};

export type AdminStats = {
  projects_total: number;
  projects_active: number;
  projects_archived: number;
  responses_total: number;
  responses_new: number;
  responses_accepted: number;
  responses_rejected: number;
  responses_by_project: ResponsesByProject[];
};
