import type { components as ProjectsContract } from "@prom/generated-contracts/projects";

type Schemas = ProjectsContract["schemas"];

export type ReportPeriod = Schemas["ReportPeriodRead"];
export type HalfYearReportPayload = Schemas["HalfYearReportPayload"];
export type HalfYearReport = Schemas["HalfYearReportRead"];
export type AdminHalfYearReport = Schemas["AdminHalfYearReportRead"];
export type CurrentReportState = Schemas["CurrentReportState"];
export type ReportPeriodPayload = Schemas["ReportPeriodCreate"];
