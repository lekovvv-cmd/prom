import { useCallback, useEffect, useState, type FormEvent } from "react";

import { useServiceDeskAccess } from "../../../providers/ServiceDeskAccessProvider";
import {
  createAccessUser,
  getAccessUsers,
  replaceUserCapabilities,
  setAccessUserActive,
  updateAccessUser,
} from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import type { ServiceDeskUser } from "../../../entities/service-desk-user/model/types";
import { getUserDirectory } from "@prom/auth/api";
import type { User } from "@prom/auth";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";
import { Input } from "@prom/ui/Input";
import { Modal } from "@prom/ui/Modal";
import { PageLayout } from "@prom/ui/PageLayout";
import { Select } from "@prom/ui/Select";
import { Table } from "@prom/ui/Table";

const capabilities = [
  "service_desk.be_assignee",
  "service_desk.approve",
  "service_desk.assign",
  "service_desk.change_priority",
  "service_desk.view_all_tickets",
  "service_desk.view_reports",
  "service_desk.manage_catalog",
  "service_desk.manage_templates",
  "service_desk.manage_approval_workflows",
  "service_desk.manage_routing",
  "service_desk.manage_sla",
  "service_desk.manage_access",
];

const labels: Record<string, string> = {
  "service_desk.be_assignee": "Работа исполнителем",
  "service_desk.approve": "Согласование",
  "service_desk.assign": "Назначение",
  "service_desk.change_priority": "Изменение приоритета",
  "service_desk.view_all_tickets": "Все заявки",
  "service_desk.view_reports": "Отчеты",
  "service_desk.manage_catalog": "Каталог",
  "service_desk.manage_templates": "Шаблоны",
  "service_desk.manage_approval_workflows": "Процессы согласования",
  "service_desk.manage_routing": "Маршрутизация",
  "service_desk.manage_sla": "SLA и календари",
  "service_desk.manage_access": "Менеджеры и права",
};

type AccessFilters = {
  q: string;
  accessType: string;
  isActive: string;
  page: number;
};

const emptyFilters: AccessFilters = {
  q: "",
  accessType: "",
  isActive: "",
  page: 1,
};

function params(filters: AccessFilters) {
  const value = new URLSearchParams({
    page_size: "10",
    page: String(filters.page),
  });
  if (filters.q.trim()) value.set("q", filters.q.trim());
  if (filters.accessType) value.set("access_type", filters.accessType);
  if (filters.isActive) value.set("is_active", filters.isActive);
  return value;
}

function userPayload(form: HTMLFormElement) {
  const data = new FormData(form);
  return {
    email: data.get("email"),
    display_name: data.get("name"),
    department: data.get("department") || null,
    position: data.get("position") || null,
    access_type: data.get("type"),
  };
}

export function ServiceDeskAdminAccessPage() {
  const { user: actor, refresh } = useServiceDeskAccess();
  const [users, setUsers] = useState<ServiceDeskUser[]>([]);
  const [filters, setFilters] = useState<AccessFilters>(emptyFilters);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [editing, setEditing] = useState<ServiceDeskUser | null>(null);
  const [projectQuery, setProjectQuery] = useState("");
  const [projectUsers, setProjectUsers] = useState<User[]>([]);
  const [selectedProjectUserId, setSelectedProjectUserId] = useState("");
  const [confirming, setConfirming] = useState<ServiceDeskUser | null>(null);
  const [confirmingAction, setConfirmingAction] = useState<{
    title: string;
    message: string;
    action: () => Promise<void>;
  } | null>(null);

  useEffect(() => {
    let active = true;
    const timeout = window.setTimeout(() => {
      void getUserDirectory(projectQuery.trim() || undefined)
        .then((items) => {
          if (active) setProjectUsers(items);
        })
        .catch((reason: unknown) => {
          if (active)
            setError(
              reason instanceof Error
                ? reason.message
                : "Не удалось загрузить пользователей UTMN",
            );
        });
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [projectQuery]);

  const load = useCallback(async () => {
    try {
      const page = await getAccessUsers(params(filters));
      setUsers(page.items);
      setPages(page.pages || 1);
      setTotal(page.total);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Ошибка доступа");
    }
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

  function updateFilter(key: keyof AccessFilters, value: string | number) {
    setFilters((current) => ({
      ...current,
      [key]: value,
      page: key === "page" ? Number(value) : 1,
    }));
  }

  async function mutate(
    action: () => Promise<ServiceDeskUser>,
    targetUserId?: string,
  ) {
    setPending(true);
    setError(null);
    try {
      await action();
      await load();
      if (targetUserId === actor?.id) await refresh();
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Изменение не сохранено",
      );
    } finally {
      setPending(false);
    }
    return false;
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const projectUser = projectUsers.find(
      (user) => user.id === selectedProjectUserId,
    );
    if (!projectUser) {
      setError("Выберите пользователя UTMN");
      return;
    }
    await mutate(async () => {
      const created = await createAccessUser({
        identity_user_id: projectUser.id,
        email: projectUser.email,
        display_name: projectUser.full_name,
        department: projectUser.department,
        position: projectUser.position,
        access_type: data.get("type"),
        capabilities: [],
      });
      form.reset();
      setSelectedProjectUserId("");
      return created;
    });
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = event.currentTarget;
    const payload = userPayload(form);
    const save = async () => {
      if (await mutate(() => updateAccessUser(editing.id, payload), editing.id))
        setEditing(null);
    };
    const dangerous =
      editing.access_type === "service_desk_admin" &&
      payload.access_type === "service_desk_manager";
    const selfChange =
      editing.id === actor?.id && payload.access_type !== editing.access_type;
    if (dangerous || selfChange) {
      setConfirmingAction({
        title: "Подтвердите изменение доступа",
        message: selfChange
          ? "После сохранения текущая страница может стать недоступной для вашего профиля."
          : "Пользователь перестанет быть администратором Service Desk, а явные права будут очищены.",
        action: save,
      });
      return;
    }
    await save();
  }

  async function toggleCapability(user: ServiceDeskUser, capability: string) {
    const next = user.capabilities.includes(capability)
      ? user.capabilities.filter((value) => value !== capability)
      : [...user.capabilities, capability];
    const save = () =>
      mutate(() => replaceUserCapabilities(user.id, next), user.id).then(
        () => undefined,
      );
    if (
      user.id === actor?.id &&
      capability === "service_desk.manage_access" &&
      !next.includes(capability)
    ) {
      setConfirmingAction({
        title: "Снять право управления доступом?",
        message:
          "После сохранения вы потеряете доступ к разделу «Менеджеры и права».",
        action: save,
      });
      return;
    }
    await save();
  }

  async function applyActiveChange() {
    if (!confirming) return;
    const target = confirming;
    setConfirming(null);
    await mutate(
      () => setAccessUserActive(target.id, !target.is_active),
      target.id,
    );
  }

  return (
    <>
      <PageLayout title="Менеджеры и права">
        <Card>
          <form
            className="service-desk-access-grant-form"
            onSubmit={(event) => void create(event)}
          >
            <Input
              label="Поиск пользователя UTMN"
              value={projectQuery}
              onChange={(event) => setProjectQuery(event.target.value)}
              placeholder="Email или имя"
            />
            <Select
              label="Пользователь UTMN"
              value={selectedProjectUserId}
              onChange={(event) => setSelectedProjectUserId(event.target.value)}
              required
            >
              <option value="">Выберите пользователя</option>
              {projectUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name} · {user.email}
                </option>
              ))}
            </Select>
            <Select name="type" label="Тип доступа">
              <option value="service_desk_manager">
                Менеджер Service Desk
              </option>
              <option value="service_desk_admin">
                Администратор Service Desk
              </option>
            </Select>
            <Button disabled={pending}>Предоставить доступ</Button>
          </form>
        </Card>

        <Card>
          <div className="filter-grid">
            <Input
              label="Поиск"
              value={filters.q}
              onChange={(event) => updateFilter("q", event.target.value)}
            />
            <Select
              label="Тип"
              value={filters.accessType}
              onChange={(event) =>
                updateFilter("accessType", event.target.value)
              }
            >
              <option value="">Все</option>
              <option value="service_desk_manager">
                Менеджеры Service Desk
              </option>
              <option value="service_desk_admin">Администраторы</option>
            </Select>
            <Select
              label="Статус"
              value={filters.isActive}
              onChange={(event) => updateFilter("isActive", event.target.value)}
            >
              <option value="">Все</option>
              <option value="true">Активные</option>
              <option value="false">Отключенные</option>
            </Select>
            <Button variant="ghost" onClick={() => setFilters(emptyFilters)}>
              Сбросить
            </Button>
          </div>

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <Table>
            <table>
              <thead>
                <tr>
                  <th>Пользователь</th>
                  <th>Тип</th>
                  <th>Права</th>
                  <th>Статус</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <strong>{user.display_name}</strong>
                      <br />
                      <small>
                        {user.email} · {user.department || "-"} ·{" "}
                        {user.position || "-"}
                      </small>
                    </td>
                    <td>
                      {user.access_type === "service_desk_admin"
                        ? "Администратор SD"
                        : "Менеджер"}
                    </td>
                    <td>
                      {user.access_type === "service_desk_admin" ? (
                        <strong>Все права Service Desk</strong>
                      ) : (
                        <div className="capability-grid">
                          {capabilities.map((capability) => (
                            <label key={capability}>
                              <input
                                type="checkbox"
                                checked={user.capabilities.includes(capability)}
                                disabled={pending}
                                onChange={() =>
                                  void toggleCapability(user, capability)
                                }
                              />
                              {labels[capability]}
                            </label>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>{user.is_active ? "Активен" : "Отключен"}</td>
                    <td>
                      <div className="table-actions">
                        <Button
                          variant="secondary"
                          disabled={pending}
                          onClick={() => setEditing(user)}
                        >
                          Изменить
                        </Button>
                        <Button
                          variant="secondary"
                          disabled={pending}
                          onClick={() => setConfirming(user)}
                        >
                          {user.is_active ? "Деактивировать" : "Активировать"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Table>
          <div className="workbench-pagination">
            <Button
              variant="secondary"
              disabled={filters.page <= 1}
              onClick={() => updateFilter("page", filters.page - 1)}
            >
              Назад
            </Button>
            <span>
              Страница {filters.page} из {pages} · {total}
            </span>
            <Button
              variant="secondary"
              disabled={filters.page >= pages}
              onClick={() => updateFilter("page", filters.page + 1)}
            >
              Далее
            </Button>
          </div>
        </Card>
      </PageLayout>

      {editing && (
        <Modal
          title="Изменить профиль доступа"
          onClose={() => setEditing(null)}
        >
          <form
            className="modal-body"
            onSubmit={(event) => void saveEdit(event)}
          >
            <Input
              name="email"
              label="Email"
              type="email"
              required
              defaultValue={editing.email}
            />
            <Input
              name="name"
              label="Имя"
              required
              defaultValue={editing.display_name}
            />
            <Input
              name="department"
              label="Подразделение"
              defaultValue={editing.department ?? ""}
            />
            <Input
              name="position"
              label="Должность"
              defaultValue={editing.position ?? ""}
            />
            <Select
              name="type"
              label="Тип доступа"
              defaultValue={editing.access_type}
            >
              <option value="service_desk_manager">
                Менеджер Service Desk
              </option>
              <option value="service_desk_admin">
                Администратор Service Desk
              </option>
            </Select>
            <div className="table-actions">
              <Button disabled={pending}>Сохранить</Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setEditing(null)}
              >
                Отмена
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {confirming && (
        <Modal
          title={
            confirming.is_active
              ? "Деактивировать доступ"
              : "Активировать доступ"
          }
          onClose={() => setConfirming(null)}
        >
          <div className="modal-body">
            <p>
              {confirming.id === actor?.id
                ? "Вы меняете собственный доступ. После сохранения права в интерфейсе будут обновлены."
                : `Подтвердите изменение доступа для ${confirming.display_name}.`}
            </p>
            <div className="table-actions">
              <Button
                disabled={pending}
                onClick={() => void applyActiveChange()}
              >
                Подтвердить
              </Button>
              <Button variant="secondary" onClick={() => setConfirming(null)}>
                Отмена
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {confirmingAction && (
        <Modal
          title={confirmingAction.title}
          onClose={() => setConfirmingAction(null)}
        >
          <div className="modal-body">
            <p>{confirmingAction.message}</p>
            <div className="table-actions">
              <Button
                disabled={pending}
                onClick={() => {
                  const action = confirmingAction.action;
                  setConfirmingAction(null);
                  void action();
                }}
              >
                Подтвердить
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setConfirmingAction(null)}
              >
                Отмена
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
