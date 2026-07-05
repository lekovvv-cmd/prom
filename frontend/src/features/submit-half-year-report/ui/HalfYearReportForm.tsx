import { CheckCircle2, FileText } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import {
  getCurrentReportState,
  submitCurrentReport
} from "../../../entities/report/api/reportApi";
import type {
  CurrentReportState,
  HalfYearReportPayload
} from "../../../entities/report/model/types";
import { formatDate } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Spinner } from "../../../shared/ui/Spinner";
import { Textarea } from "../../../shared/ui/Textarea";

const emptyReportForm: HalfYearReportPayload = {
  completed_work: "",
  project_results: "",
  competencies_used: "",
  difficulties: "",
  next_period_plans: ""
};

function reportToForm(state: CurrentReportState): HalfYearReportPayload {
  return {
    completed_work: state.report?.completed_work ?? "",
    project_results: state.report?.project_results ?? "",
    competencies_used: state.report?.competencies_used ?? "",
    difficulties: state.report?.difficulties ?? "",
    next_period_plans: state.report?.next_period_plans ?? ""
  };
}

function normalizeReportPayload(form: HalfYearReportPayload): HalfYearReportPayload {
  return {
    completed_work: form.completed_work.trim(),
    project_results: form.project_results?.trim() || null,
    competencies_used: form.competencies_used?.trim() || null,
    difficulties: form.difficulties?.trim() || null,
    next_period_plans: form.next_period_plans?.trim() || null
  };
}

function periodDates(state: CurrentReportState) {
  const period = state.active_period;
  if (!period) {
    return null;
  }
  if (!period.starts_on && !period.ends_on) {
    return "Даты не указаны";
  }
  return `${period.starts_on ? formatDate(period.starts_on) : "Без даты"} - ${
    period.ends_on ? formatDate(period.ends_on) : "без даты"
  }`;
}

export function HalfYearReportForm() {
  const [state, setState] = useState<CurrentReportState | null>(null);
  const [form, setForm] = useState<HalfYearReportPayload>(emptyReportForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    getCurrentReportState()
      .then((nextState) => {
        if (!isMounted) {
          return;
        }
        setState(nextState);
        setForm(reportToForm(nextState));
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить полугодовой отчёт");
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

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = normalizeReportPayload(form);
    if (payload.completed_work.length < 3) {
      setError("Выполненная работа: опишите работу минимум 3 символами");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      setMessage(null);
      const report = await submitCurrentReport(payload);
      setState((current) => (current ? { ...current, report } : current));
      setForm({
        completed_work: report.completed_work,
        project_results: report.project_results ?? "",
        competencies_used: report.competencies_used ?? "",
        difficulties: report.difficulties ?? "",
        next_period_plans: report.next_period_plans ?? ""
      });
      setMessage("Полугодовой отчёт сохранён");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить отчёт");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <Spinner label="Загружаем полугодовой отчёт" />;
  }

  if (!state?.active_period) {
    return (
      <Card className="report-card">
        <div className="report-empty">
          <FileText size={24} />
          <div>
            <h2>Полугодовой отчёт</h2>
            <p>Период отчётности пока не открыт администратором.</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="report-card">
      <div className="section-heading">
        <div>
          <span>Полугодовой отчёт</span>
          <h2>{state.active_period.title}</h2>
          <p>{periodDates(state)}</p>
        </div>
        {state.report && (
          <span className="report-status">
            <CheckCircle2 size={16} />
            Отчёт подан
          </span>
        )}
      </div>
      {message && (
        <div className="form-success form-success-card" role="status" aria-live="polite">
          <CheckCircle2 size={22} />
          <div>
            <strong>{message}</strong>
            <span>Можно вернуться в профиль и обновить отчёт до закрытия периода.</span>
          </div>
        </div>
      )}
      <form className="report-form" onSubmit={handleSubmit}>
        <Textarea
          label="Выполненная работа"
          name="completed_work"
          rows={5}
          value={form.completed_work}
          onChange={(event) => setForm({ ...form, completed_work: event.target.value })}
          required
        />
        <Textarea
          label="Результаты по проектам"
          name="project_results"
          rows={4}
          value={form.project_results ?? ""}
          onChange={(event) => setForm({ ...form, project_results: event.target.value })}
        />
        <Textarea
          label="Использованные компетенции"
          name="competencies_used"
          rows={3}
          value={form.competencies_used ?? ""}
          onChange={(event) => setForm({ ...form, competencies_used: event.target.value })}
        />
        <div className="form-grid">
          <Textarea
            label="Сложности"
            name="difficulties"
            rows={4}
            value={form.difficulties ?? ""}
            onChange={(event) => setForm({ ...form, difficulties: event.target.value })}
          />
          <Textarea
            label="Планы на следующий период"
            name="next_period_plans"
            rows={4}
            value={form.next_period_plans ?? ""}
            onChange={(event) => setForm({ ...form, next_period_plans: event.target.value })}
          />
        </div>
        {error && <p className="form-error">{error}</p>}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Сохраняем" : state.report ? "Обновить отчёт" : "Подать отчёт"}
        </Button>
      </form>
    </Card>
  );
}
