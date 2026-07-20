import { apiClient } from "@prom/api-client";
import { filterDefaultCompetencies } from "../lib/defaultCompetencies";
import type { Competency } from "../model/types";

export function getCompetencies(search?: string) {
  const params = new URLSearchParams();
  if (search) {
    params.set("search", search);
  }
  const query = params.toString();
  return apiClient
    .request<Competency[]>(`/competencies${query ? `?${query}` : ""}`, {
      auth: false,
    })
    .catch(() => filterDefaultCompetencies(search));
}
