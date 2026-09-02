import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@prom/auth";
import { CompetencyPicker } from "../../../entities/competency/ui/CompetencyPicker";
import {
  getProjectProfile,
  updateProjectProfile,
} from "../../../entities/user/api/projectUserApi";
import type {
  ProjectUser,
  ProjectUserProfilePayload,
} from "../../../entities/user/model/types";
import { HalfYearReportForm } from "../../../features/submit-half-year-report/ui/HalfYearReportForm";
import { AdminReportControl } from "../../../widgets/admin-report-control/ui/AdminReportControl";
import { Header } from "@prom/layout";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";
import { Input } from "@prom/ui/Input";
import { PageLayout } from "@prom/ui/PageLayout";
import { Textarea } from "@prom/ui/Textarea";

export function ProfilePage() {
  const { isAdmin, user } = useAuth();
  const [profile, setProfile] = useState<ProjectUser | null>(null);
  const [form, setForm] = useState<ProjectUserProfilePayload>({
    full_name: "",
    department: "",
    position: "",
    competencies: "",
    about: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    void getProjectProfile()
      .then((nextProfile) => {
        if (!active) return;
        setProfile(nextProfile);
        setForm({
          full_name: nextProfile.full_name,
          department: nextProfile.department ?? "",
          position: nextProfile.position ?? "",
          competencies: nextProfile.competencies ?? "",
          about: nextProfile.about ?? "",
        });
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Не удалось загрузить профиль",
          );
      });
    return () => {
      active = false;
    };
  }, []);

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
      const nextProfile = await updateProjectProfile({
        full_name: form.full_name.trim(),
        department: form.department?.trim() || null,
        position: form.position?.trim() || null,
        competencies: form.competencies?.trim() || null,
        about: form.about?.trim() || null,
      });
      setProfile(nextProfile);
      setMessage("Профиль сохранён");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось сохранить профиль",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header />
      <PageLayout title="Профиль">
        <Card className="profile-card">
          <form className="profile-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <Input
                label="ФИО"
                name="full_name"
                value={form.full_name}
                onChange={(event) =>
                  setForm({ ...form, full_name: event.target.value })
                }
                required
              />
              <Input
                label="Email"
                name="email"
                value={profile?.email ?? user?.email ?? ""}
                disabled
              />
            </div>
            <div className="form-grid">
              <Input
                label="Подразделение"
                name="department"
                value={form.department ?? ""}
                onChange={(event) =>
                  setForm({ ...form, department: event.target.value })
                }
                placeholder="Например: ШПИУ"
              />
              <Input
                label="Должность"
                name="position"
                value={form.position ?? ""}
                onChange={(event) =>
                  setForm({ ...form, position: event.target.value })
                }
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
              onChange={(event) =>
                setForm({ ...form, about: event.target.value })
              }
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
