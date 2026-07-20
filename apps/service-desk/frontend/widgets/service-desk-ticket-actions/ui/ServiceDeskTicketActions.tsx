import { useEffect, useState } from "react";
import {
  Archive,
  Check,
  CirclePlay,
  MessageSquare,
  UserRound,
  X,
} from "lucide-react";

import { getWorkbenchUsers } from "../../../entities/service-desk-workbench/api/serviceDeskWorkbenchApi";
import {
  changeServiceDeskTicketPriority,
  performServiceDeskTicketAction,
} from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import { getServiceDeskActionLabel } from "../../../entities/service-desk-ticket/lib/serviceDeskLabels";
import type {
  ServiceDeskAllowedAction,
  ServiceDeskPriority,
  ServiceDeskTicket,
} from "../../../entities/service-desk-ticket/model/types";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";
import { Modal } from "@prom/ui/Modal";
import { Select } from "@prom/ui/Select";

const actionIcons: Partial<Record<ServiceDeskAllowedAction, typeof Check>> = {
  approve: Check,
  reject: X,
  assign: UserRound,
  reassign: UserRound,
  start: CirclePlay,
  request_clarification: MessageSquare,
  wait_external: Archive,
  resolve: Check,
  close: Archive,
  cancel: X,
};
const textActions = new Set<ServiceDeskAllowedAction>([
  "request_clarification",
  "wait_external",
  "resolve",
  "cancel",
]);

export function ServiceDeskTicketActions({
  ticket,
  onTicketChanged,
}: {
  ticket: ServiceDeskTicket;
  onTicketChanged: (ticket: ServiceDeskTicket) => void;
}) {
  const [selected, setSelected] = useState<ServiceDeskAllowedAction | null>(
    null,
  );
  const [payload, setPayload] = useState("");
  const [priority, setPriority] = useState<ServiceDeskPriority>(
    ticket.priority,
  );
  const [assignees, setAssignees] = useState<
    Array<{ id: string; display_name: string }>
  >([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (
      ticket.allowed_actions.some(
        (action) => action === "assign" || action === "reassign",
      )
    )
      void getWorkbenchUsers(true)
        .then(setAssignees)
        .catch(() => setAssignees([]));
  }, [ticket.allowed_actions]);

  async function submit() {
    if (!selected) return;
    const isAssignment = selected === "assign" || selected === "reassign";
    if (
      (isAssignment ||
        textActions.has(selected) ||
        selected === "change_priority") &&
      !payload.trim()
    ) {
      setError(
        isAssignment ? "Выберите исполнителя" : "Укажите причину изменения",
      );
      return;
    }
    setPending(true);
    setError(null);
    try {
      const body = isAssignment
        ? { assignee_user_id: payload }
        : selected === "request_clarification"
          ? { comment: payload.trim() }
          : selected === "wait_external" || selected === "cancel"
            ? { reason: payload.trim() }
            : selected === "resolve"
              ? { resolution_summary: payload.trim() }
              : {};
      onTicketChanged(
        selected === "change_priority"
          ? await changeServiceDeskTicketPriority(
              ticket.id,
              priority,
              payload.trim(),
            )
          : await performServiceDeskTicketAction(
              ticket.id,
              selected,
              body as Record<string, string>,
            ),
      );
      setSelected(null);
      setPayload("");
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Не удалось выполнить действие",
      );
    } finally {
      setPending(false);
    }
  }

  const executableActions = ticket.allowed_actions.filter(
    (action) => action !== "approve" && action !== "reject",
  );
  return (
    <Card className="service-desk-ticket-actions">
      <div className="service-desk-section-heading">
        <div>
          <span className="service-desk-eyebrow">Доступные действия</span>
          <h3>Следующий шаг</h3>
        </div>
      </div>
      <div className="button-row ticket-action-row">
        {executableActions.map((action) => {
          const Icon = actionIcons[action] ?? Check;
          return (
            <Button
              key={action}
              variant={action === "cancel" ? "danger" : "secondary"}
              onClick={() => {
                setSelected(action);
                setPayload("");
                setPriority(ticket.priority);
                setError(null);
              }}
            >
              <Icon size={16} aria-hidden="true" />
              {getServiceDeskActionLabel(action)}
            </Button>
          );
        })}
      </div>
      {executableActions.length === 0 ? (
        <p className="muted">Сейчас действий для вашей роли нет.</p>
      ) : null}
      {selected ? (
        <Modal
          title={getServiceDeskActionLabel(selected)}
          onClose={() => setSelected(null)}
        >
          <div className="modal-body">
            {selected === "change_priority" ? (
              <>
                <Select
                  label="Новый приоритет"
                  value={priority}
                  onChange={(event) =>
                    setPriority(event.target.value as ServiceDeskPriority)
                  }
                >
                  <option value="low">Низкий</option>
                  <option value="medium">Средний</option>
                  <option value="high">Высокий</option>
                  <option value="critical">Критический</option>
                </Select>
                <label className="field">
                  <span>Причина</span>
                  <textarea
                    value={payload}
                    onChange={(event) => setPayload(event.target.value)}
                    minLength={2}
                    maxLength={2000}
                    rows={4}
                    required
                  />
                </label>
              </>
            ) : selected === "assign" || selected === "reassign" ? (
              <Select
                label="Исполнитель"
                value={payload}
                onChange={(event) => setPayload(event.target.value)}
              >
                <option value="">Выберите исполнителя</option>
                {assignees.map((assignee) => (
                  <option key={assignee.id} value={assignee.id}>
                    {assignee.display_name}
                  </option>
                ))}
              </Select>
            ) : selected === "start" ||
              selected === "resume" ||
              selected === "close" ? (
              <p>
                Подтвердите действие для заявки {ticket.number ?? "без номера"}.
              </p>
            ) : (
              <label className="field">
                <span>
                  {selected === "resolve" ? "Итог выполнения" : "Комментарий"}
                </span>
                <textarea
                  value={payload}
                  onChange={(event) => setPayload(event.target.value)}
                  minLength={2}
                  maxLength={5000}
                  rows={4}
                  required
                />
              </label>
            )}
            {error ? (
              <p className="form-error" role="alert">
                {error}
              </p>
            ) : null}
            <div className="button-row">
              <Button disabled={pending} onClick={() => void submit()}>
                {pending ? "Выполняем..." : "Подтвердить"}
              </Button>
              <Button variant="secondary" onClick={() => setSelected(null)}>
                Отмена
              </Button>
            </div>
          </div>
        </Modal>
      ) : null}
    </Card>
  );
}
