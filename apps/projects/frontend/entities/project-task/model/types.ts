import type { components as ProjectsContract } from "@prom/generated-contracts/projects";

import type { Attachment } from "../../project/model/types";

type Schemas = ProjectsContract["schemas"];

export type ProjectTaskStatus = Schemas["ProjectTaskStatus"];
export type ProjectTask = Omit<Schemas["ProjectTaskRead"], "attachments"> & {
  attachments: Attachment[];
};
export type ProjectStage = Schemas["ProjectStageRead"];
export type ProjectStageWithTasks = Omit<
  Schemas["ProjectStageWithTasksRead"],
  "tasks"
> & {
  tasks: ProjectTask[];
};
export type ProjectStagePayload = Omit<
  Schemas["ProjectStageCreate"],
  "position"
> & {
  position?: number;
};
export type ProjectTaskPayload = Omit<
  Schemas["ProjectTaskCreate"],
  "status"
> & {
  status?: ProjectTaskStatus;
};
