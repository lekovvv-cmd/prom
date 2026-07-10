import { useState, type FormEvent } from "react";
import { Lock, MessageSquare, Send } from "lucide-react";

import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { addTicketComment } from "../../../features/add-ticket-comment/api/addTicketComment";
import { formatDateTime } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Select } from "../../../shared/ui/Select";
import { Textarea } from "../../../shared/ui/Textarea";

const FINAL_STATUSES = new Set(["closed", "cancelled"]);

export function ServiceDeskTicketComments({
  currentUser,
  ticket,
  onTicketChanged
}: {
  currentUser: { id: string; access_type: "manager" | "service_desk_admin"; capabilities: string[] };
  ticket: ServiceDeskTicket;
  onTicketChanged: () => Promise<void>;
}) {
  const [body, setBody] = useState("");
  const [visibility, setVisibility] = useState<"public" | "internal">("public");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const canAddInternal =
    currentUser.access_type === "service_desk_admin" ||
    currentUser.id === ticket.assignee_user_id ||
    currentUser.capabilities.includes("service_desk.view_all_tickets");
  const isLocked = FINAL_STATUSES.has(ticket.status);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedBody = body.trim();
    if (normalizedBody.length < 2) {
      setError("Введите комментарий не короче 2 символов");
      return;
    }
    try {
      setIsSubmitting(true);
      setError(null);
      await addTicketComment(ticket.id, { body: normalizedBody, visibility });
      setBody("");
      setVisibility("public");
      await onTicketChanged();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось добавить комментарий");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="service-desk-comments">
      <div className="service-desk-section-heading">
        <div>
          <span className="service-desk-eyebrow">Коммуникация</span>
          <h3>Комментарии</h3>
        </div>
        <MessageSquare size={19} aria-hidden="true" />
      </div>

      {ticket.comments.length === 0 ? (
        <p className="muted">Комментариев пока нет.</p>
      ) : (
        <ol className="service-desk-comment-list">
          {ticket.comments.map((comment) => (
            <li className={comment.visibility === "internal" ? "service-desk-comment-internal" : ""} key={comment.id}>
              <div className="service-desk-comment-meta">
                <strong>{comment.author.display_name}</strong>
                <span>{formatDateTime(comment.created_at)}</span>
                {comment.visibility === "internal" ? (
                  <span className="service-desk-comment-visibility"><Lock size={12} /> Внутренний</span>
                ) : null}
              </div>
              <p>{comment.body}</p>
              {comment.updated_at ? <span className="muted">Изменён</span> : null}
            </li>
          ))}
        </ol>
      )}

      {isLocked ? (
        <p className="muted">В закрытую или отменённую заявку комментарии добавить нельзя.</p>
      ) : (
        <form className="service-desk-comment-form" onSubmit={handleSubmit}>
          <Textarea
            label="Комментарий"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            maxLength={5000}
            placeholder="Напишите сообщение по заявке"
            required
          />
          {canAddInternal ? (
            <Select
              label="Видимость"
              value={visibility}
              onChange={(event) => setVisibility(event.target.value as "public" | "internal")}
            >
              <option value="public">Публичный — виден заявителю</option>
              <option value="internal">Внутренний — только для Service Desk</option>
            </Select>
          ) : null}
          {error ? <p className="form-error">{error}</p> : null}
          <div className="button-row">
            <Button type="submit" disabled={isSubmitting}>
              <Send size={16} /> {isSubmitting ? "Отправляем…" : "Добавить комментарий"}
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}
