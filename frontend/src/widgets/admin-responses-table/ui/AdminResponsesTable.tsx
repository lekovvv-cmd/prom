import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import { splitCompetencies } from "../../../entities/competency/lib/competencies";
import type { ProjectResponse } from "../../../entities/project-response/model/types";
import { ResponseStatusBadge } from "../../../entities/project-response/ui/ResponseStatusBadge";
import { ResponseStatusSelect } from "../../../features/update-response-status/ui/ResponseStatusSelect";
import { formatDateTime } from "../../../shared/lib/date";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Table } from "../../../shared/ui/Table";

export function AdminResponsesTable({
  responses,
  onUpdated
}: {
  responses: ProjectResponse[];
  onUpdated: () => void;
}) {
  if (responses.length === 0) {
    return <EmptyState title="Откликов нет" text="Новые отклики появятся после отправки формы сотрудником." />;
  }

  return (
    <Table>
      <table>
        <thead>
          <tr>
            <th>Проект</th>
            <th>Сотрудник</th>
            <th>Комментарий</th>
            <th>Компетенции</th>
            <th>Файлы</th>
            <th>Статус</th>
            <th>Изменить</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {responses.map((response) => (
            <tr key={response.id}>
              <td>{response.project_title}</td>
              <td>
                <strong>{response.full_name}</strong>
                <span>{response.email}</span>
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
              <td>
                <ResponseStatusSelect responseId={response.id} value={response.status} onUpdated={onUpdated} />
              </td>
              <td>{formatDateTime(response.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Table>
  );
}
