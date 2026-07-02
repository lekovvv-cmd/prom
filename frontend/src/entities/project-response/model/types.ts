import type { Attachment } from "../../project/model/types";

export type ProjectResponseStatus = "new" | "viewed" | "contacted" | "accepted" | "rejected" | "cancelled";

export type ProjectResponse = {
  id: string;
  project_id: string;
  project_title?: string;
  full_name: string;
  email: string;
  comment: string | null;
  competencies: string | null;
  attachments: Attachment[];
  status: ProjectResponseStatus;
  created_at: string;
  processed_by?: string | null;
  processed_at?: string | null;
};

export type ProjectResponsePayload = {
  full_name: string;
  email: string;
  comment?: string | null;
  competencies?: string | null;
};
