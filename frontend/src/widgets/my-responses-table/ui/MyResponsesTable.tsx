import { Link } from "react-router-dom";

import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import { splitCompetencies } from "../../../entities/competency/lib/competencies";
import type { ProjectResponse } from "../../../entities/project-response/model/types";
import { ResponseStatusBadge } from "../../../entities/project-response/ui/ResponseStatusBadge";
import { WithdrawProjectResponseButton } from "../../../features/withdraw-project-response/ui/WithdrawProjectResponseButton";
import { formatDateTime } from "../../../shared/lib/date";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Table } from "../../../shared/ui/Table";

export function MyResponsesTable({
  responses,
  onUpdated
}: {
  responses: ProjectResponse[];
  onUpdated: () => void;
}) {
  if (responses.length === 0) {
    return (
      <EmptyState
        title="Откликов пока нет"
        text="Откройте проект в витрине и отправьте заявку, чтобы отслеживать её статус здесь."
      />
    );
  }

  return (
    <Table>
      <table>
        <thead>
          <tr>
            <th>Проект</th>
            <th>Комментарий</th>
            <th>Компетенции</th>
            <th>Файлы</th>
            <th>Статус</th>
            <th>Дата</th>
            <th>Действие</th>
          </tr>
        </thead>
        <tbody>
          {responses.map((response) => (
            <tr key={response.id}>
              <td>
                <Link className="table-link" to={`/projects/${response.project_id}`}>
                  {response.project_title ?? "Проект"}
                </Link>
              </td>
              <td>{response.comment ?? "Без комментария"}</td>
              <td>
                <div className="competency-inline">
                  {splitCompetencies(response.competencies).map((competency) => (
                    <span className="chip" key={competency}>
                      {competency}
                    </span>
                  ))}
                </div>
              </td>
              <td>
                <AttachmentList attachments={response.attachments} />
              </td>
              <td>
                <ResponseStatusBadge status={response.status} />
              </td>
              <td>{formatDateTime(response.created_at)}</td>
              <td>
                <WithdrawProjectResponseButton
                  responseId={response.id}
                  status={response.status}
                  onWithdrawn={onUpdated}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Table>
  );
}
