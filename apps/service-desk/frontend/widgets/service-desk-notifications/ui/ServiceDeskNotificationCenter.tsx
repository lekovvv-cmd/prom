import { Bell, CheckCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  getServiceDeskNotifications,
  getServiceDeskUnreadCount,
  markAllServiceDeskNotificationsRead,
  markServiceDeskNotificationRead,
} from "../../../entities/service-desk-notification/api/serviceDeskNotificationApi";
import type { ServiceDeskNotification } from "../../../entities/service-desk-notification/model/types";
import { formatDateTime } from "@prom/utils/date";
import { Button } from "@prom/ui/Button";
import { EmptyState } from "@prom/ui/EmptyState";
import { Spinner } from "@prom/ui/Spinner";

export function NotificationList({
  notifications,
  onRead,
}: {
  notifications: ServiceDeskNotification[];
  onRead: (notification: ServiceDeskNotification) => void;
}) {
  if (!notifications.length) {
    return (
      <EmptyState
        title="Уведомлений нет"
        text="Здесь появятся события по заявкам Service Desk."
      />
    );
  }
  return (
    <div className="notification-list">
      {notifications.map((notification) => (
        <article
          className={`notification-item ${notification.is_read ? "is-read" : "is-unread"}`}
          key={notification.id}
        >
          <div>
            <strong>{notification.title}</strong>
            <p>{notification.body}</p>
            <small>{formatDateTime(notification.created_at)}</small>
          </div>
          <div className="notification-actions">
            {!notification.is_read && (
              <Button variant="ghost" onClick={() => onRead(notification)}>
                Прочитано
              </Button>
            )}
            {notification.ticket_id && (
              <Link
                className="button button-secondary"
                onClick={() => onRead(notification)}
                to={`/service-desk/tickets/${notification.ticket_id}`}
              >
                Открыть заявку
              </Link>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

export function ServiceDeskNotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<ServiceDeskNotification[]>(
    [],
  );
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async (withList = false) => {
    try {
      if (withList) setIsLoading(true);
      setError(null);
      const [count, list] = await Promise.all([
        getServiceDeskUnreadCount(),
        withList ? getServiceDeskNotifications() : Promise.resolve(null),
      ]);
      setUnreadCount(count.count);
      if (list) setNotifications(list);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Не удалось загрузить уведомления",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(false);
  }, [load]);
  useEffect(() => {
    function close(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function openCenter() {
    const next = !isOpen;
    setIsOpen(next);
    if (next) await load(true);
  }
  async function markRead(notification: ServiceDeskNotification) {
    if (notification.is_read) return;
    const updated = await markServiceDeskNotificationRead(notification.id);
    setNotifications((items) =>
      items.map((item) => (item.id === updated.id ? updated : item)),
    );
    setUnreadCount((count) => Math.max(0, count - 1));
  }
  async function markAll() {
    await markAllServiceDeskNotificationsRead();
    setNotifications((items) =>
      items.map((item) => ({ ...item, is_read: true })),
    );
    setUnreadCount(0);
  }

  return (
    <div className="notification-center" ref={rootRef}>
      <Button
        className="notification-trigger"
        variant="ghost"
        aria-expanded={isOpen}
        aria-label="Уведомления Service Desk"
        onClick={() => void openCenter()}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="notification-count">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </Button>
      {isOpen && (
        <section className="notification-panel" aria-label="Центр уведомлений">
          <div className="notification-panel-header">
            <div>
              <strong>Уведомления</strong>
              <small>
                {unreadCount
                  ? `Непрочитанных: ${unreadCount}`
                  : "Всё прочитано"}
              </small>
            </div>
            {unreadCount > 0 && (
              <Button variant="ghost" onClick={() => void markAll()}>
                <CheckCheck size={15} />
                Прочитать все
              </Button>
            )}
          </div>
          {isLoading ? (
            <Spinner label="Загружаем уведомления" />
          ) : error ? (
            <div className="notification-error">
              <p>{error}</p>
              <Button variant="secondary" onClick={() => void load(true)}>
                Повторить
              </Button>
            </div>
          ) : (
            <NotificationList
              notifications={notifications}
              onRead={(item) => void markRead(item)}
            />
          )}
        </section>
      )}
    </div>
  );
}
