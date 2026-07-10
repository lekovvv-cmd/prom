import { useState, type FormEvent } from "react";
import { XCircle } from "lucide-react";

import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { Button } from "../../../shared/ui/Button";
import { Modal } from "../../../shared/ui/Modal";
import { Textarea } from "../../../shared/ui/Textarea";
import { rejectTicket } from "../api/rejectTicket";

export function RejectTicketButton({
  approvalId,
  ticketId,
  onCompleted
}: {
  approvalId: string;
  ticketId: string;
  onCompleted: (ticket: ServiceDeskTicket) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedComment = comment.trim();
    if (normalizedComment.length < 2) {
      setError("Укажите причину отклонения");
      return;
    }
    try {
      setIsSubmitting(true);
      setError(null);
      const ticket = await rejectTicket(ticketId, approvalId, normalizedComment);
      setIsOpen(false);
      setComment("");
      onCompleted(ticket);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось отклонить заявку");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Button variant="danger" onClick={() => setIsOpen(true)}>
        <XCircle size={16} />
        Отклонить
      </Button>
      {isOpen && (
        <Modal title="Отклонить заявку" onClose={() => setIsOpen(false)}>
          <form className="form-panel" onSubmit={handleSubmit}>
            <p className="muted">Причина обязательна и будет видна в истории заявки.</p>
            <Textarea
              label="Причина отклонения"
              value={comment}
              required
              maxLength={2000}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Опишите, что необходимо исправить"
            />
            {error && <p className="form-error">{error}</p>}
            <div className="button-row">
              <Button type="submit" variant="danger" disabled={isSubmitting}>
                {isSubmitting ? "Сохраняем..." : "Подтвердить отклонение"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setIsOpen(false)}>
                Отмена
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
