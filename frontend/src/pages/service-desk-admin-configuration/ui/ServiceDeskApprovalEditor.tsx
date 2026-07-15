import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowUp, Check, Plus, Save, Trash2, X } from "lucide-react";

import type { ServiceDeskService } from "../../../entities/service-desk-catalog/model/types";
import { getServiceDeskUserOptions, type ServiceDeskUserOption } from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import {
  applyAdminServiceApprovalConfiguration,
  getAdminServiceApprovalConfiguration,
  listAdminServices
} from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import type { ApprovalWorkflowApplyPayload, ServiceApprovalConfiguration } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";

type ApprovalMode = "none" | "workflow";
type DraftStage = {
  id: string;
  title: string;
  decision_rule: "any" | "all";
  approverIds: string[];
};

const defaultWorkflowName = "Согласование заявки";
const networkErrorPattern = /failed to fetch|network(?:\s+request)?\s+failed|networkerror/i;

function errorText(reason: unknown, fallback: string) {
  if (reason instanceof Error && networkErrorPattern.test(reason.message)) {
    return "Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.";
  }
  return reason instanceof Error ? reason.message : fallback;
}

export function ServiceDeskApprovalEditor() {
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [users, setUsers] = useState<ServiceDeskUserOption[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [configuration, setConfiguration] = useState<ServiceApprovalConfiguration | null>(null);
  const [mode, setMode] = useState<ApprovalMode>("none");
  const [workflowName, setWorkflowName] = useState(defaultWorkflowName);
  const [stages, setStages] = useState<DraftStage[]>([]);
  const [newStageTitle, setNewStageTitle] = useState("");
  const [newStageRule, setNewStageRule] = useState<"any" | "all">("all");
  const [selectedApprovers, setSelectedApprovers] = useState<Record<string, string>>({});
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [canRetryOptions, setCanRetryOptions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const stageSequence = useRef(0);

  async function loadOptions() {
    setError(null);
    setCanRetryOptions(false);
    setLoadingOptions(true);
    try {
      const [nextServices, nextUsers] = await Promise.all([listAdminServices(), getServiceDeskUserOptions("service_desk.approve")]);
      setServices(nextServices);
      setUsers(nextUsers);
    } catch (reason) {
      setCanRetryOptions(true);
      setError(errorText(reason, "Не удалось загрузить данные согласований"));
    } finally {
      setLoadingOptions(false);
    }
  }

  useEffect(() => { void loadOptions(); }, []);

  function hydrate(next: ServiceApprovalConfiguration) {
    setConfiguration(next);
    setMode(next.approval_mode);
    setWorkflowName(next.workflow?.name ?? defaultWorkflowName);
    setStages((next.workflow?.stages ?? []).map((stage) => ({
      id: stage.id,
      title: stage.title,
      decision_rule: stage.decision_rule,
      approverIds: stage.approvers.map((approver) => approver.service_desk_user_id)
    })));
    setSelectedApprovers({});
  }

  async function selectService(nextServiceId: string) {
    setServiceId(nextServiceId);
    setConfiguration(null);
    setError(null);
    setSuccess(null);
    setStages([]);
    if (!nextServiceId) return;
    setLoading(true);
    try {
      hydrate(await getAdminServiceApprovalConfiguration(nextServiceId));
    } catch (reason) {
      setError(errorText(reason, "Не удалось загрузить опубликованную версию формы"));
    } finally {
      setLoading(false);
    }
  }

  function addStage() {
    if (!newStageTitle.trim()) return;
    stageSequence.current += 1;
    setStages((current) => [...current, {
      id: `new-stage-${stageSequence.current}`,
      title: newStageTitle.trim(),
      decision_rule: newStageRule,
      approverIds: []
    }]);
    setNewStageTitle("");
  }

  function updateStage(stageId: string, patch: Partial<DraftStage>) {
    setStages((current) => current.map((stage) => stage.id === stageId ? { ...stage, ...patch } : stage));
  }

  function moveStage(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= stages.length) return;
    setStages((current) => {
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function removeStage(stageId: string) {
    setStages((current) => current.filter((stage) => stage.id !== stageId));
    setSelectedApprovers((current) => {
      const next = { ...current };
      delete next[stageId];
      return next;
    });
  }

  function addApprover(stageId: string) {
    const userId = selectedApprovers[stageId];
    if (!userId) return;
    setStages((current) => current.map((stage) => stage.id === stageId && !stage.approverIds.includes(userId)
      ? { ...stage, approverIds: [...stage.approverIds, userId] }
      : stage));
    setSelectedApprovers((current) => ({ ...current, [stageId]: "" }));
  }

  function removeApprover(stageId: string, userId: string) {
    setStages((current) => current.map((stage) => stage.id === stageId
      ? { ...stage, approverIds: stage.approverIds.filter((id) => id !== userId) }
      : stage));
  }

  const canApply = Boolean(serviceId) && !saving && (mode === "none" || (
    workflowName.trim().length >= 2
    && stages.length > 0
    && stages.every((stage) => stage.title.trim().length >= 2 && stage.approverIds.length > 0)
  ));

  async function apply() {
    if (!serviceId || !canApply) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    const payload: ApprovalWorkflowApplyPayload = {
      approval_mode: mode,
      name: workflowName.trim() || defaultWorkflowName,
      stages: mode === "workflow" ? stages.map((stage) => ({
        title: stage.title.trim(),
        decision_rule: stage.decision_rule,
        approver_user_ids: stage.approverIds
      })) : []
    };
    try {
      const applied = await applyAdminServiceApprovalConfiguration(serviceId, payload);
      hydrate(applied);
      setSuccess(`Версия ${applied.template_version.version} опубликована. Предыдущая версия перенесена в архив.`);
    } catch (reason) {
      setError(errorText(reason, "Не удалось применить согласование"));
    } finally {
      setSaving(false);
    }
  }

  return <PageLayout title="Согласования" subtitle="Настройте процесс для услуги и примените его одной новой версией формы.">
    {error ? <div className="form-error config-error" role="alert"><span>{error}</span>{canRetryOptions ? <Button type="button" variant="ghost" onClick={() => void loadOptions()} disabled={loadingOptions}>Повторить</Button> : null}</div> : null}
    {success ? <p className="success-text" role="status">{success}</p> : null}
    <Card className="approval-apply-selector">
      <Select label="Услуга" value={serviceId} onChange={(event) => void selectService(event.target.value)} disabled={loadingOptions || canRetryOptions}>
        <option value="">Выберите услугу</option>
        {services.map((service) => <option key={service.id} value={service.id}>{service.title}</option>)}
      </Select>
    </Card>

    {loading ? <Spinner label="Загружаем настройки согласования" /> : null}
    {configuration ? <Card className="approval-apply-card">
      <div className="service-desk-section-heading">
        <div>
          <h3>Опубликованная версия {configuration.template_version.version}</h3>
          <p className="muted">Поля и настройки формы будут скопированы автоматически.</p>
        </div>
        <div className="button-row approval-mode-actions">
          <Button variant={mode === "workflow" ? "secondary" : "primary"} aria-pressed={mode === "workflow"} onClick={() => setMode(mode === "workflow" ? "none" : "workflow")}>
            {mode === "workflow" ? <><X size={16} />Отключить согласование</> : <><Check size={16} />Включить согласование</>}
          </Button>
        </div>
      </div>

      {mode === "workflow" ? <div className="approval-apply-workflow">
        <Input label="Название процесса" value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} />
        <div className="service-desk-section-heading">
          <div><h3>Этапы</h3><p className="muted">Каждому этапу нужен хотя бы один согласующий.</p></div>
        </div>
        <div className="admin-config-form-grid approval-new-stage">
          <Input label="Название нового этапа" value={newStageTitle} onChange={(event) => setNewStageTitle(event.target.value)} />
          <Select label="Правило нового этапа" value={newStageRule} onChange={(event) => setNewStageRule(event.target.value as "any" | "all")}>
            <option value="all">Нужны все</option>
            <option value="any">Достаточно одного</option>
          </Select>
          <Button onClick={addStage} disabled={!newStageTitle.trim()}><Plus size={16} />Добавить этап</Button>
        </div>
        {stages.length ? <div className="approval-draft-stage-list">
          {stages.map((stage, index) => <div className="approval-draft-stage" key={stage.id}>
            <div className="approval-draft-stage-heading">
              <strong>Этап {index + 1}</strong>
              <span className="button-row">
                <Button variant="ghost" aria-label="Поднять этап" onClick={() => moveStage(index, -1)} disabled={index === 0}><ArrowUp size={16} /></Button>
                <Button variant="ghost" aria-label="Опустить этап" onClick={() => moveStage(index, 1)} disabled={index === stages.length - 1}><ArrowDown size={16} /></Button>
                <Button variant="ghost" aria-label="Удалить этап" onClick={() => removeStage(stage.id)}><Trash2 size={16} /></Button>
              </span>
            </div>
            <div className="admin-config-form-grid">
              <Input label={`Название этапа ${index + 1}`} value={stage.title} onChange={(event) => updateStage(stage.id, { title: event.target.value })} />
              <Select label={`Правило этапа ${index + 1}`} value={stage.decision_rule} onChange={(event) => updateStage(stage.id, { decision_rule: event.target.value as "any" | "all" })}>
                <option value="all">Нужны все</option>
                <option value="any">Достаточно одного</option>
              </Select>
            </div>
            <div className="approval-draft-approvers">
              <Select label={`Добавить согласующего к этапу ${index + 1}`} value={selectedApprovers[stage.id] ?? ""} onChange={(event) => setSelectedApprovers((current) => ({ ...current, [stage.id]: event.target.value }))}>
                <option value="">Выберите согласующего</option>
                {users.filter((user) => !stage.approverIds.includes(user.id)).map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}
              </Select>
              <Button className="approval-add-approver" variant="secondary" onClick={() => addApprover(stage.id)} disabled={!selectedApprovers[stage.id]}><Plus size={16} />Добавить согласующего</Button>
              <div className="approval-draft-approver-tags">
                {stage.approverIds.map((userId) => {
                  const user = users.find((candidate) => candidate.id === userId);
                  return <span className="approval-approver-tag" key={userId}><span>{user?.display_name ?? "Согласующий"}</span><button type="button" aria-label={`Удалить согласующего ${user?.display_name ?? ""}`} onClick={() => removeApprover(stage.id, userId)}>×</button></span>;
                })}
              </div>
            </div>
          </div>)}
        </div> : <p className="muted">Добавьте хотя бы один этап согласования.</p>}
      </div> : <p className="muted">Новые заявки будут создаваться без согласования.</p>}

      <div className="approval-apply-footer">
        <p className="approval-apply-warning">Изменения применятся только к новым заявкам.</p>
        <Button onClick={() => void apply()} disabled={!canApply}><Save size={16} />{saving ? "Применяем…" : "Сохранить и применить"}</Button>
      </div>
    </Card> : null}
  </PageLayout>;
}
