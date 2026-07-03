import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { useAuth } from "../../../app/providers/AppProviders";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { CompetencyPicker } from "../../../entities/competency/ui/CompetencyPicker";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { Textarea } from "../../../shared/ui/Textarea";
import { isUtmnEmail, normalizeEmail } from "../../../shared/lib/email";
import { submitProjectResponseWithFiles } from "../api/submitProjectResponse";
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
  const { user } = useAuth();
  const [form, setForm] = useState({
    ...initialState,
    full_name: user?.full_name ?? "",
    email: user?.email ?? initialState.email
  });
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function validateForm() {
    if (form.full_name.trim().length < 2) {
      return "Укажите ФИО не короче 2 символов";
    }
    if (!form.email.trim()) {
      return "Укажите email";
    }
    if (!isUtmnEmail(form.email)) {
      return "Email: введите корректный адрес на домене @utmn.ru";
    }
    return null;
  }

  if (user?.role === "admin") {
    return (
      <section className="form-panel" id="response-form" aria-live="polite">
        <h2>Отклики недоступны</h2>
        <p className="muted">Администратор обрабатывает отклики и не может отправлять заявки на проекты.</p>
      </section>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      setSuccess(false);
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await submitProjectResponseWithFiles(projectId, {
        full_name: form.full_name.trim(),
        email: normalizeEmail(form.email),
        comment: form.comment || null,
        competencies: form.competencies || null
      }, files);
      setForm({
        ...initialState,
        full_name: user?.full_name ?? "",
        email: user?.email ?? initialState.email
      });
      setFiles([]);
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
      <CompetencyPicker
        label="Мои компетенции"
        value={form.competencies}
        onChange={(competencies) => setForm({ ...form, competencies })}
      />
      <FileInput files={files} label="Прикрепить файлы к отклику" onChange={setFiles} />
      {error && <p className="form-error">{error}</p>}
      {success && <p className="form-success">Отклик отправлен. Администратор увидит его в панели.</p>}
      <Button type="submit" disabled={isSubmitting}>
        <Send size={18} />
        {isSubmitting ? "Отправляем" : "Отправить отклик"}
      </Button>
    </form>
  );
}
