import type { components as ProjectsContract } from "@prom/generated-contracts/projects";

type Schemas = ProjectsContract["schemas"];

/** Projects-owned profile, including its local role and profile fields. */
export type ProjectUser = Schemas["UserRead"];
export type ProjectUserProfilePayload = Schemas["UserProfileUpdate"];
