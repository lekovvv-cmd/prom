import { CalendarCheck, CheckCircle2, FileText, Lock } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  closeAdminReportPeriod,
  getAdminReportPeriods,
  getAdminReports,
  openAdminReportPeriod
} from "../../../entities/report/api/reportApi";
import type {
  AdminHalfYearReport,
  ReportPeriod,
  ReportPeriodPayload
} from "../../../entities/report/model/types";
import { formatDate, formatDateTime } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { Spinner } from "../../../shared/ui/Spinner";

const defaultPeriodForm: ReportPeriodPayload = {
  title: "Полугодовой отчёт 2026, первое полугодие",
  starts_on: "",
  ends_on: ""
};

function formatPeriodDates(period: ReportPeriod) {
  if (!period.starts_on && !period.ends_on) {
    return "Даты не указаны";
  }
  return `${period.starts_on ? formatDate(period.starts_on) : "Без даты"} - ${
    period.ends_on ? formatDate(period.ends_on) : "без даты"
  }`;
}

function normalizePeriodPayload(form: ReportPeriodPayload): ReportPeriodPayload {
  return {
    title: form.title.trim(),
    starts_on: form.starts_on || null,
    ends_on: form.ends_on || null
  };
}

export function AdminReportControl() {
  const [periods, setPeriods] = useState<ReportPeriod[]>([]);
  const [reports, setReports] = useState<AdminHalfYearReport[]>([]);
  const [form, setForm] = useState<ReportPeriodPayload>(defaultPeriodForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const activePeriod = useMemo(() => periods.find((period) => period.status === "open") ?? null, [periods]);

  async function reload() {
    const [nextPeriods, nextReports] = await Promise.all([getAdminReportPeriods(), getAdminReports()]);
    setPeriods(nextPeriods);
    setReports(nextReports);
  }

  useEffect(() => {
    let isMounted = true;
    reload()
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить отчёты");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleOpenPeriod(event: FormEvent) {
    event.preventDefault();
    const payload = normalizePeriodPayload(form);
    if (payload.title.length < 3) {
      setError("Название периода: укажите минимум 3 символа");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      setMessage(null);
      await openAdminReportPeriod(payload);
      await reload();
      setMessage("Период отчётности открыт");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось открыть период");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleClosePeriod(periodId: string) {
    try {
      setIsSubmitting(true);
      setError(null);
      setMessage(null);
      await closeAdminReportPeriod(periodId);
      await reload();
      setMessage("Период отчётности закрыт");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось закрыть период");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <Spinner label="Загружаем управление отчётами" />;
  }

  return (
    <Card className="report-card admin-report-card">
      <div className="section-heading">
        <div>
          <span>Администрирование</span>
          <h2>Полугодовые отчёты</h2>
          <p>Администратор открывает период вручную. Сотрудники и руководители подают отчёты в профиле.</p>
        </div>
        {activePeriod ? (
          <span className="report-status">
            <CalendarCheck size={16} />
            Период открыт
          </span>
        ) : (
          <span className="report-status report-status-muted">
            <Lock size={16} />
            Период закрыт
          </span>
        )}
      </div>
      <form className="report-admin-form" onSubmit={handleOpenPeriod}>
        <Input
          label="Название периода"
          name="report_period_title"
          value={form.title}
          onChange={(event) => setForm({ ...form, title: event.target.value })}
          required
        />
        <Input
          label="Начало"
          name="report_period_starts_on"
          type="date"
          value={form.starts_on ?? ""}
          onChange={(event) => setForm({ ...form, starts_on: event.target.value })}
        />
        <Input
          label="Окончание"
          name="report_period_ends_on"
          type="date"
          value={form.ends_on ?? ""}
          onChange={(event) => setForm({ ...form, ends_on: event.target.value })}
        />
        <Button type="submit" disabled={isSubmitting}>
          Открыть период
        </Button>
      </form>
      {activePeriod && (
        <div className="report-active-period">
          <div>
            <strong>{activePeriod.title}</strong>
            <span>{formatPeriodDates(activePeriod)}</span>
          </div>
          <Button variant="secondary" type="button" disabled={isSubmitting} onClick={() => handleClosePeriod(activePeriod.id)}>
            Закрыть период
          </Button>
        </div>
      )}
      {message && (
        <p className="form-success">
          <CheckCircle2 size={16} />
          {message}
        </p>
      )}
      {error && <p className="form-error">{error}</p>}
      <div className="report-submissions">
        <div className="section-heading compact">
          <div>
            <span>Поданные отчёты</span>
            <h3>{reports.length} в списке</h3>
          </div>
        </div>
        {reports.length === 0 ? (
          <div className="empty-state">
            <FileText size={24} />
            <h3>Отчётов пока нет</h3>
            <p>Они появятся после отправки формы сотрудником или руководителем.</p>
          </div>
        ) : (
          <div className="report-list">
            {reports.map((report) => (
              <article className="report-list-item" key={report.id}>
                <div>
                  <strong>{report.user.full_name}</strong>
                  <span>{report.user.email}</span>
                  <small>{report.period.title}</small>
                </div>
                <p>{report.completed_work}</p>
                <time>{formatDateTime(report.updated_at)}</time>
              </article>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
