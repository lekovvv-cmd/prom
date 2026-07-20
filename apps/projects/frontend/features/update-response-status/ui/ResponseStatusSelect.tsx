import type { ProjectResponseStatus } from "../../../entities/project-response/model/types";
import { responseStatusLabels } from "../../../entities/project-response/ui/ResponseStatusBadge";
import { Select } from "@prom/ui/Select";
import { updateResponseStatus } from "../api/updateResponseStatus";

const statuses: ProjectResponseStatus[] = [
  "new",
  "viewed",
  "contacted",
  "accepted",
  "rejected",
  "cancelled",
];

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
      onChange={(event) =>
        void handleChange(event.target.value as ProjectResponseStatus)
      }
    >
      {statuses.map((status) => (
        <option key={status} value={status}>
          {responseStatusLabels[status]}
        </option>
      ))}
    </Select>
  );
}
