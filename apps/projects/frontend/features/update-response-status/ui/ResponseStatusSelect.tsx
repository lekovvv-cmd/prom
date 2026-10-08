import type { ProjectResponseStatus } from "../../../entities/project-response/model/types";
import { responseStatusLabels } from "../../../entities/project-response/ui/ResponseStatusBadge";
import { Select } from "@prom/ui/Select";
import { updateResponseStatus } from "../api/updateResponseStatus";

const transitions: Record<ProjectResponseStatus, ProjectResponseStatus[]> = {
  new: ["viewed", "contacted", "accepted", "rejected", "cancelled"],
  viewed: ["contacted", "accepted", "rejected", "cancelled"],
  contacted: ["accepted", "rejected", "cancelled"],
  accepted: [],
  rejected: [],
  cancelled: [],
};

export function ResponseStatusSelect({
  responseId,
  value,
  onUpdated,
}: {
  responseId: string;
  value: ProjectResponseStatus;
  onUpdated: () => void;
}) {
  async function handleChange(status: ProjectResponseStatus) {
    await updateResponseStatus(responseId, status);
    onUpdated();
  }

  return (
    <Select
      name={`status-${responseId}`}
      value={value}
      disabled={transitions[value].length === 0}
      onChange={(event) =>
        void handleChange(event.target.value as ProjectResponseStatus)
      }
    >
      {[value, ...transitions[value]].map((status) => (
        <option key={status} value={status}>
          {responseStatusLabels[status]}
        </option>
      ))}
    </Select>
  );
}
