import { useEffect, useState, type FormEvent } from "react";
import { Download, Lock, MessageSquare, Paperclip, Pencil, Send, Trash2 } from "lucide-react";

import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { addTicketComment } from "../../../features/add-ticket-comment/api/addTicketComment";
import { deleteServiceDeskComment, downloadServiceDeskAttachment, listServiceDeskCommentAttachments, updateServiceDeskComment, uploadServiceDeskCommentAttachment } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskAttachment } from "../../../entities/service-desk-ticket/model/types";
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
  currentUser: { id: string; access_type: "service_desk_manager" | "service_desk_admin"; capabilities: string[] };
  ticket: ServiceDeskTicket;
  onTicketChanged: () => Promise<void>;
}) {
  const [body, setBody] = useState("");
  const [visibility, setVisibility] = useState<"public" | "internal">("public");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingBody, setEditingBody] = useState("");
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

  async function saveEdit(commentId: string) {
    if (editingBody.trim().length < 2) { setError("Введите комментарий не короче 2 символов"); return; }
    try { await updateServiceDeskComment(ticket.id, commentId, editingBody.trim()); setEditingId(null); setEditingBody(""); await onTicketChanged(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Не удалось изменить комментарий"); }
  }

  async function removeComment(commentId: string) {
    if (!window.confirm("Удалить комментарий?")) return;
    try { await deleteServiceDeskComment(ticket.id, commentId); await onTicketChanged(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Не удалось удалить комментарий"); }
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
              {editingId === comment.id ? <div className="service-desk-comment-form"><Textarea label="Комментарий" value={editingBody} onChange={(event) => setEditingBody(event.target.value)} maxLength={5000} /><div className="button-row"><Button onClick={() => void saveEdit(comment.id)}>Сохранить</Button><Button variant="ghost" onClick={() => setEditingId(null)}>Отмена</Button></div></div> : <p>{comment.body}</p>}
              {!isLocked && (comment.author_user_id === currentUser.id || currentUser.access_type === "service_desk_admin") ? <div className="button-row"><Button variant="ghost" onClick={() => { setEditingId(comment.id); setEditingBody(comment.body); }}><Pencil size={14} />Изменить</Button><Button variant="ghost" onClick={() => void removeComment(comment.id)}><Trash2 size={14} />Удалить</Button></div> : null}
              <CommentAttachments ticketId={ticket.id} commentId={comment.id} canUpload={!isLocked && (comment.author_user_id === currentUser.id || currentUser.access_type === "service_desk_admin")} />
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

function CommentAttachments({ ticketId, commentId, canUpload }: { ticketId: string; commentId: string; canUpload: boolean }) {
  const [attachments, setAttachments] = useState<ServiceDeskAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { void listServiceDeskCommentAttachments(ticketId, commentId).then(setAttachments).catch(() => undefined); }, [commentId, ticketId]);
  async function upload(file: File) { try { const attachment = await uploadServiceDeskCommentAttachment(ticketId, commentId, file); setAttachments((current) => [...current, attachment]); } catch (reason: unknown) { setError(reason instanceof Error ? reason.message : "Не удалось загрузить файл"); } }
  async function download(attachment: ServiceDeskAttachment) { try { const blob = await downloadServiceDeskAttachment(ticketId, attachment.id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = attachment.file_name; link.click(); URL.revokeObjectURL(url); } catch (reason: unknown) { setError(reason instanceof Error ? reason.message : "Не удалось скачать файл"); } }
  return <div className="comment-attachments">{attachments.map((attachment) => <button className="comment-attachment" type="button" key={attachment.id} onClick={() => void download(attachment)}><Download size={13} aria-hidden="true" />{attachment.file_name}</button>)}{canUpload ? <label className="comment-attachment-upload"><Paperclip size={13} aria-hidden="true" />Прикрепить файл<input type="file" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); event.target.value = ""; }} /></label> : null}{error ? <small className="field-error">{error}</small> : null}</div>;
}
