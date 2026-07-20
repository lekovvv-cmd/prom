import { useState, type FormEvent } from "react";
import { CheckCircle2 } from "lucide-react";

import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { Button } from "@prom/ui/Button";
import { Modal } from "@prom/ui/Modal";
import { Textarea } from "@prom/ui/Textarea";
import { approveTicket } from "../api/approveTicket";

export function ApproveTicketButton({
  approvalId,
  ticketId,
  onCompleted,
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
    try {
      setIsSubmitting(true);
      setError(null);
      const ticket = await approveTicket(ticketId, approvalId, comment.trim());
      setIsOpen(false);
      setComment("");
      onCompleted(ticket);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Не удалось согласовать заявку",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        <CheckCircle2 size={16} />
        Согласовать
      </Button>
      {isOpen && (
        <Modal title="Согласовать заявку" onClose={() => setIsOpen(false)}>
          <form className="form-panel" onSubmit={handleSubmit}>
            <p className="muted">
              Комментарий необязателен и будет сохранён в истории решения.
            </p>
            <Textarea
              label="Комментарий"
              value={comment}
              maxLength={2000}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Например: согласовано без замечаний"
            />
            {error && <p className="form-error">{error}</p>}
            <div className="button-row">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Сохраняем..." : "Подтвердить согласование"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsOpen(false)}
              >
                Отмена
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
