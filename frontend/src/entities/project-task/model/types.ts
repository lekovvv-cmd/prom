import type { Attachment } from "../../project/model/types";
import type { User } from "../../user/model/types";

export type ProjectTaskStatus = "todo" | "in_progress" | "done" | "cancelled";

export type ProjectTask = {
  id: string;
  project_id: string;
  stage_id: string | null;
  title: string;
  description: string | null;
  assignee: Pick<User, "id" | "email" | "full_name"> | null;
  status: ProjectTaskStatus;
  due_date: string | null;
  is_overdue: boolean;
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
};

export type ProjectStage = {
  id: string;
  project_id: string;
  title: string;
  position: number;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectStageWithTasks = ProjectStage & {
  tasks: ProjectTask[];
};

export type ProjectStagePayload = {
  title: string;
  position?: number;
  start_date?: string | null;
  end_date?: string | null;
};

export type ProjectTaskPayload = {
  title: string;
  description?: string | null;
  stage_id?: string | null;
  assignee_user_id?: string | null;
  status?: ProjectTaskStatus;
  due_date?: string | null;
};
