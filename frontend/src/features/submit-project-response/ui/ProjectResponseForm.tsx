import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { Textarea } from "../../../shared/ui/Textarea";
import { submitProjectResponse } from "../api/submitProjectResponse";
import type { ResponseFormState } from "../model/types";

const initialState: ResponseFormState = {
  full_name: "",
  email: "employee@utmn.ru",
  comment: "",
  competencies: ""
};

export function ProjectResponseForm({
  projectId,
  onSubmitted
}: {
  projectId: string;
  onSubmitted: () => void;
}) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      setError(null);
      await submitProjectResponse(projectId, {
        full_name: form.full_name,
        email: form.email,
        comment: form.comment || null,
        competencies: form.competencies || null
      });
      setForm(initialState);
      setSuccess(true);
      onSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить отклик");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-panel" id="response-form" onSubmit={handleSubmit}>
      <h2>Откликнуться на проект</h2>
      <div className="form-grid">
        <Input
          label="ФИО"
          name="full_name"
          value={form.full_name}
          onChange={(event) => setForm({ ...form, full_name: event.target.value })}
          required
        />
        <Input
          label="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          required
        />
      </div>
      <Textarea
        label="Комментарий"
        name="comment"
        value={form.comment}
        onChange={(event) => setForm({ ...form, comment: event.target.value })}
        rows={4}
      />
      <Textarea
        label="Компетенции"
        name="competencies"
        value={form.competencies}
        onChange={(event) => setForm({ ...form, competencies: event.target.value })}
        rows={3}
      />
      {error && <p className="form-error">{error}</p>}
      {success && <p className="form-success">Отклик отправлен. Администратор увидит его в панели.</p>}
      <Button type="submit" disabled={isSubmitting}>
        <Send size={18} />
        {isSubmitting ? "Отправляем" : "Отправить отклик"}
      </Button>
    </form>
  );
}
