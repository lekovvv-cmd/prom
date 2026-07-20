import { useEffect, useState } from "react";
import { Download, Paperclip, Trash2, Upload } from "lucide-react";

import {
  deleteServiceDeskAttachment,
  downloadServiceDeskAttachment,
  listServiceDeskAttachments,
  uploadServiceDeskTicketAttachment,
} from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskAttachment } from "../../../entities/service-desk-ticket/model/types";
import { formatDateTime } from "@prom/utils/date";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";

function formatSize(value: number) {
  return value < 1024 * 1024
    ? `${Math.max(1, Math.round(value / 1024))} КБ`
    : `${(value / 1024 / 1024).toFixed(1)} МБ`;
}

export function ServiceDeskTicketAttachments({
  ticketId,
  canUpload = true,
  canDelete = false,
  onChanged,
}: {
  ticketId: string;
  canUpload?: boolean;
  canDelete?: boolean;
  onChanged?: (attachments: ServiceDeskAttachment[]) => void;
}) {
  const [attachments, setAttachments] = useState<ServiceDeskAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function load() {
    try {
      const items = await listServiceDeskAttachments(ticketId);
      setAttachments(items);
      onChanged?.(items);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Не удалось загрузить вложения",
      );
    }
  }
  useEffect(() => {
    void load();
  }, [ticketId]);

  async function upload(file: File) {
    setUploading(true);
    setError(null);
    try {
      await uploadServiceDeskTicketAttachment(ticketId, file);
      await load();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error ? reason.message : "Не удалось загрузить файл",
      );
    } finally {
      setUploading(false);
    }
  }
  async function download(attachment: ServiceDeskAttachment) {
    try {
      const blob = await downloadServiceDeskAttachment(ticketId, attachment.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = attachment.file_name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error ? reason.message : "Не удалось скачать файл",
      );
    }
  }
  async function remove(attachment: ServiceDeskAttachment) {
    if (!window.confirm(`Удалить файл «${attachment.file_name}»?`)) return;
    try {
      await deleteServiceDeskAttachment(ticketId, attachment.id);
      await load();
    } catch (reason: unknown) {
      setError(
        reason instanceof Error ? reason.message : "Не удалось удалить файл",
      );
    }
  }

  return (
    <Card className="service-desk-attachments">
      <div className="service-desk-section-heading">
        <div>
          <span className="service-desk-eyebrow">
            <Paperclip size={14} aria-hidden="true" /> Файлы
          </span>
          <h3>Вложения</h3>
        </div>
        {canUpload ? (
          <label className="button button-secondary">
            <Upload size={16} aria-hidden="true" />
            {uploading ? "Загружаем..." : "Добавить файл"}
            <input
              type="file"
              hidden
              disabled={uploading}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void upload(file);
                event.target.value = "";
              }}
            />
          </label>
        ) : null}
      </div>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      {attachments.length ? (
        <ul className="service-desk-attachment-list">
          {attachments.map((attachment) => (
            <li key={attachment.id}>
              <div>
                <strong>{attachment.file_name}</strong>
                <small>
                  {attachment.content_type ?? "Файл"} ·{" "}
                  {formatSize(attachment.size_bytes)} ·{" "}
                  {formatDateTime(attachment.created_at)}
                </small>
              </div>
              <div className="table-actions">
                <Button
                  variant="ghost"
                  aria-label={`Скачать ${attachment.file_name}`}
                  onClick={() => void download(attachment)}
                >
                  <Download size={16} aria-hidden="true" />
                </Button>
                {canDelete ? (
                  <Button
                    variant="ghost"
                    aria-label={`Удалить ${attachment.file_name}`}
                    onClick={() => void remove(attachment)}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">Вложений пока нет.</p>
      )}
    </Card>
  );
}
