import { FormEvent, useState } from "react";

import { useAuth } from "../../../app/providers/AppProviders";
import { CompetencyPicker } from "../../../entities/competency/ui/CompetencyPicker";
import { updateMyProfile } from "../../../entities/user/api/userApi";
import type { UserProfilePayload } from "../../../entities/user/model/types";
import { HalfYearReportForm } from "../../../features/submit-half-year-report/ui/HalfYearReportForm";
import { AdminReportControl } from "../../../widgets/admin-report-control/ui/AdminReportControl";
import { Header } from "../../../widgets/header/ui/Header";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Textarea } from "../../../shared/ui/Textarea";

export function ProfilePage() {
  const { isAdmin, refreshUser, user } = useAuth();
  const [form, setForm] = useState<UserProfilePayload>({
    full_name: user?.full_name ?? "",
    department: user?.department ?? "",
    position: user?.position ?? "",
    competencies: user?.competencies ?? "",
    about: user?.about ?? ""
  });
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (form.full_name.trim().length < 2) {
      setError("ФИО: укажите минимум 2 символа");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      setMessage(null);
      await updateMyProfile({
        full_name: form.full_name.trim(),
        department: form.department?.trim() || null,
        position: form.position?.trim() || null,
        competencies: form.competencies?.trim() || null,
        about: form.about?.trim() || null
      });
      await refreshUser();
      setMessage("Профиль сохранён");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить профиль");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header />
      <PageLayout title="Профиль" subtitle="Компетенции из профиля используются при подборе сотрудников в проекты">
        <Card className="profile-card">
          <form className="profile-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <Input
                label="ФИО"
                name="full_name"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                required
              />
              <Input label="Email" name="email" value={user?.email ?? ""} disabled />
            </div>
            <div className="form-grid">
              <Input
                label="Подразделение"
                name="department"
                value={form.department ?? ""}
                onChange={(event) => setForm({ ...form, department: event.target.value })}
                placeholder="Например: ШПИУ"
              />
              <Input
                label="Должность"
                name="position"
                value={form.position ?? ""}
                onChange={(event) => setForm({ ...form, position: event.target.value })}
                placeholder="Например: аналитик данных"
              />
            </div>
            <CompetencyPicker
              label="Мои компетенции"
              value={form.competencies}
              onChange={(competencies) => setForm({ ...form, competencies })}
            />
            <Textarea
              label="О себе"
              name="about"
              rows={4}
              value={form.about ?? ""}
              onChange={(event) => setForm({ ...form, about: event.target.value })}
              placeholder="Опыт, интересы, ограничения по участию в проектах"
            />
            {error && <p className="form-error">{error}</p>}
            {message && <p className="form-success">{message}</p>}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Сохраняем" : "Сохранить профиль"}
            </Button>
          </form>
        </Card>
        {isAdmin ? <AdminReportControl /> : <HalfYearReportForm />}
      </PageLayout>
    </>
  );
}
