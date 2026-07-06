import { FileCheck2, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { splitCompetencies } from "../../../entities/competency/lib/competencies";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { Textarea } from "../../../shared/ui/Textarea";
import { isUtmnEmail, normalizeEmail } from "../../../shared/lib/email";
import { submitProjectResponseWithFiles } from "../api/submitProjectResponse";
import type { ResponseFormState } from "../model/types";

const initialState: ResponseFormState = {
  full_name: "",
  email: "employee@utmn.ru",
  comment: ""
};

export function ProjectResponseForm({
  projectId,
  onSubmitted
}: {
  projectId: string;
  onSubmitted: () => void;
}) {
  const { isLoading, user } = useAuth();
  const [form, setForm] = useState({
    ...initialState,
    full_name: user?.full_name ?? "",
    email: user?.email ?? initialState.email
  });
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      setForm((current) => ({
        ...current,
        full_name: user.full_name,
        email: user.email
      }));
    }
  }, [user]);

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
    if (user && normalizeEmail(form.email) !== user.email) {
      return "Email должен совпадать с авторизованным пользователем";
    }
    return null;
  }

  if (isLoading) {
    return (
      <section className="form-panel" id="response-form" aria-live="polite">
        <h2>Проверяем авторизацию</h2>
        <p className="muted">Форма отклика будет доступна после проверки пользователя.</p>
      </section>
    );
  }

  if (!user) {
    return (
      <section className="form-panel" id="response-form" aria-live="polite">
        <h2>Войдите, чтобы откликнуться</h2>
        <p className="muted">Отклик можно отправить только от авторизованного пользователя ТюмГУ.</p>
        <Link className="button button-primary" to="/login">
          Войти
        </Link>
      </section>
    );
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
        competencies: user?.competencies || null
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
      <div className="profile-competencies-readonly" aria-label="Компетенции из профиля">
        <strong>Компетенции из профиля</strong>
        {splitCompetencies(user.competencies).length > 0 ? (
          <div className="chip-list">
            {splitCompetencies(user.competencies).map((competency) => (
              <span className="chip" key={competency}>
                {competency}
              </span>
            ))}
          </div>
        ) : (
          <span className="muted">Не указаны</span>
        )}
      </div>
      <FileInput files={files} label="Прикрепить файлы к отклику" onChange={setFiles} />
      {error && <p className="form-error">{error}</p>}
      {success && (
        <div className="form-success form-success-card" role="status" aria-live="polite">
          <FileCheck2 size={22} />
          <div>
            <strong>Отклик отправлен</strong>
            <span>Заявка уже в очереди обработки. Администратор увидит её в панели откликов.</span>
          </div>
        </div>
      )}
      <Button type="submit" disabled={isSubmitting}>
        <Send size={18} />
        {isSubmitting ? "Отправляем" : "Отправить отклик"}
      </Button>
    </form>
  );
}
