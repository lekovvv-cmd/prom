import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp, Pencil, Plus, Save, Trash2 } from "lucide-react";

import type { ServiceDeskService } from "../../../entities/service-desk-catalog/model/types";
import { getServiceDeskUserOptions, type ServiceDeskUserOption } from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import { addAdminApprover, configureAdminApproval, createAdminApprovalStage, deleteAdminApprover, deleteAdminApprovalStage, getAdminApprovalConfiguration, listAdminServices, listAdminTemplateVersions, reorderAdminApprovalStages, updateAdminApprovalStage } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import type { AdminTemplateVersion, ApprovalConfiguration } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";

type ApprovalStage = NonNullable<ApprovalConfiguration["workflow"]>["stages"][number];

export function ServiceDeskApprovalEditor() {
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [versions, setVersions] = useState<AdminTemplateVersion[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [config, setConfig] = useState<ApprovalConfiguration | null>(null);
  const [users, setUsers] = useState<ServiceDeskUserOption[]>([]);
  const [stageTitle, setStageTitle] = useState("");
  const [rule, setRule] = useState<"any" | "all">("all");
  const [approver, setApprover] = useState("");
  const [editingStageId, setEditingStageId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingRule, setEditingRule] = useState<"any" | "all">("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { listAdminServices().then(setServices).catch((reason) => setError(errorText(reason, "Не удалось загрузить услуги"))); getServiceDeskUserOptions("service_desk.approve").then(setUsers).catch((reason) => setError(errorText(reason, "Не удалось загрузить список согласующих"))); }, []);
  async function loadVersions(nextService: string) { setServiceId(nextService); setVersionId(""); setConfig(null); if (!nextService) { setVersions([]); return; } try { setVersions(await listAdminTemplateVersions(nextService)); } catch (reason) { setError(errorText(reason, "Не удалось загрузить версии форм")); } }
  async function loadConfig(nextVersion: string) { setVersionId(nextVersion); try { setConfig(await getAdminApprovalConfiguration(nextVersion)); } catch (reason) { setError(errorText(reason, "Не удалось загрузить процесс согласования")); } }
  async function mutate(action: () => Promise<ApprovalConfiguration>) { try { setConfig(await action()); } catch (reason) { setError(errorText(reason, "Не удалось сохранить изменения")); } }
  async function addStage() { if (!config?.workflow || !stageTitle.trim()) return; await mutate(() => createAdminApprovalStage(config.workflow!.id, { title: stageTitle.trim(), decision_rule: rule })); setStageTitle(""); }
  async function editStage(stage: ApprovalStage) { setEditingStageId(stage.id); setEditingTitle(stage.title); setEditingRule(stage.decision_rule); }
  async function saveStage(stageId: string) { await mutate(() => updateAdminApprovalStage(stageId, { title: editingTitle.trim(), decision_rule: editingRule })); setEditingStageId(null); }
  async function moveStage(index: number, delta: number) { if (!config?.workflow) return; const stages = [...config.workflow.stages]; const target = index + delta; if (target < 0 || target >= stages.length) return; [stages[index], stages[target]] = [stages[target], stages[index]]; await mutate(() => reorderAdminApprovalStages(config.workflow!.id, stages.map((stage) => stage.id))); }
  async function removeStage(stageId: string) { await mutate(() => deleteAdminApprovalStage(stageId).then(() => getAdminApprovalConfiguration(versionId))); }
  async function addApprover(stageId: string) { if (!approver) return; await mutate(() => addAdminApprover(stageId, approver)); setApprover(""); }
  async function removeApprover(approverId: string) { await mutate(() => deleteAdminApprover(approverId).then(() => getAdminApprovalConfiguration(versionId))); }
  return <PageLayout title="Согласования" subtitle="Этапы, правила и пользователи, которым разрешено согласовывать заявки.">{error ? <p className="form-error" role="alert">{error}</p> : null}<Card><Select label="Услуга" value={serviceId} onChange={(event) => void loadVersions(event.target.value)}><option value="">Выберите услугу</option>{services.map((service) => <option key={service.id} value={service.id}>{service.title}</option>)}</Select><Select label="Версия формы" value={versionId} onChange={(event) => void loadConfig(event.target.value)}><option value="">Выберите версию</option>{versions.map((version) => <option key={version.id} value={version.id}>{versionLabel(version)}</option>)}</Select></Card>{config ? <Card><h3>Процесс согласования</h3><p className="muted">{config.approval_mode === "workflow" ? "По этапам" : "Без согласования"}</p><Button variant="secondary" onClick={() => void mutate(() => configureAdminApproval(versionId, { approval_mode: config.approval_mode === "workflow" ? "none" : "workflow", name: "Согласование заявки", is_active: config.approval_mode !== "workflow" }))}>{config.approval_mode === "workflow" ? "Отключить процесс" : "Включить процесс по этапам"}</Button>{config.workflow ? <><div className="admin-config-form-grid"><Input label="Название нового этапа" value={stageTitle} onChange={(event) => setStageTitle(event.target.value)} /><Select label="Правило нового этапа" value={rule} onChange={(event) => setRule(event.target.value as "any" | "all")}><option value="all">Нужны все</option><option value="any">Достаточно одного</option></Select><Button onClick={() => void addStage()} disabled={!stageTitle.trim()}><Plus size={15} />Добавить этап</Button></div><div className="admin-config-list">{config.workflow.stages.map((stage, index) => editingStageId === stage.id ? <div className="admin-config-row" key={stage.id}><Input label="Название этапа" value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} /><Select label="Правило" value={editingRule} onChange={(event) => setEditingRule(event.target.value as "any" | "all")}><option value="all">Нужны все</option><option value="any">Достаточно одного</option></Select><Button onClick={() => void saveStage(stage.id)}><Save size={15} />Сохранить</Button></div> : <div className="admin-config-row approval-stage-row" key={stage.id}><span><strong>{index + 1}. {stage.title}</strong><small>{stage.decision_rule === "all" ? "Нужны все" : "Достаточно одного"} · {stage.approvers.length} согласующих</small></span><span className="button-row approval-stage-actions"><Button variant="ghost" onClick={() => void editStage(stage)}><Pencil size={15} />Изменить</Button><Button variant="ghost" onClick={() => void moveStage(index, -1)} disabled={index === 0}><ArrowUp size={15} /></Button><Button variant="ghost" onClick={() => void moveStage(index, 1)} disabled={index === config.workflow!.stages.length - 1}><ArrowDown size={15} /></Button><Button variant="ghost" onClick={() => void removeStage(stage.id)}><Trash2 size={15} />Удалить</Button><Select aria-label="Согласующий" value={approver} onChange={(event) => setApprover(event.target.value)}><option value="">Выберите согласующего</option>{users.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}</Select><Button className="approval-add-approver" onClick={() => void addApprover(stage.id)} disabled={!approver}><Plus size={15} />Добавить согласующего</Button></span><div>{stage.approvers.map((item) => { const user = users.find((candidate) => candidate.id === item.service_desk_user_id); return <span className="tag" key={item.id}>{user?.display_name ?? "Согласующий"}{user?.department || user?.position ? " · " + [user.department, user.position].filter(Boolean).join(", ") : ""}<button type="button" aria-label="Удалить согласующего" onClick={() => void removeApprover(item.id)}>×</button></span>; })}</div></div>)}</div></> : null}</Card> : null}</PageLayout>;
}

function versionLabel(version: AdminTemplateVersion) { return "Версия " + version.version + " · " + (version.status === "draft" ? "Черновая версия" : version.status === "published" ? "Опубликовано" : "Архив"); }
function errorText(reason: unknown, fallback: string) { return reason instanceof Error ? reason.message : fallback; }
