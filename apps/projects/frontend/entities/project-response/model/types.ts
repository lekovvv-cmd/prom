import type { components as ProjectsContract } from "@prom/generated-contracts/projects";

type Schemas = ProjectsContract["schemas"];

export type ProjectResponseStatus = Schemas["ProjectResponseStatus"];
export type ProjectResponse = Schemas["ProjectResponseRead"] &
  Partial<
    Pick<
      Schemas["AdminProjectResponseRead"],
      "processed_at" | "processed_by" | "project_title"
    >
  >;
export type ProjectResponsePayload = Schemas["ProjectResponseCreate"];
