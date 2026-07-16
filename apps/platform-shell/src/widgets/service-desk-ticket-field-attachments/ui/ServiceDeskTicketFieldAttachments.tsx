import { useEffect, useState } from "react";
import { Download, Paperclip, Trash2 } from "lucide-react";

import { deleteServiceDeskAttachment, downloadServiceDeskAttachment, listServiceDeskFieldAttachments } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskAttachment } from "../../../entities/service-desk-ticket/model/types";
import { Card } from "../../../shared/ui/Card";

export function ServiceDeskTicketFieldAttachments({ ticketId, fields, canDelete = false }: { ticketId: string; fields: Array<{ key: string; label: string; type: string }>; canDelete?: boolean }) {
  const fileFields = fields.filter((field) => field.type === "file");
  const fieldKeys = fileFields.map((field) => field.key).join("|");
  const [attachments, setAttachments] = useState<Record<string, ServiceDeskAttachment[]>>({});
  useEffect(() => { let active = true; Promise.all(fileFields.map(async (field) => [field.key, await listServiceDeskFieldAttachments(ticketId, field.key)] as const)).then((items) => { if (active) setAttachments(Object.fromEntries(items)); }).catch(() => undefined); return () => { active = false; }; }, [ticketId, fieldKeys]);
  if (!fileFields.some((field) => (attachments[field.key] ?? []).length)) return null;
  async function download(attachment: ServiceDeskAttachment) { const blob = await downloadServiceDeskAttachment(ticketId, attachment.id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = attachment.file_name; link.click(); URL.revokeObjectURL(url); }
  async function remove(fieldKey: string, attachment: ServiceDeskAttachment) { if (!window.confirm(`Удалить файл «${attachment.file_name}»?`)) return; await deleteServiceDeskAttachment(ticketId, attachment.id); setAttachments((current) => ({ ...current, [fieldKey]: (current[fieldKey] ?? []).filter((item) => item.id !== attachment.id) })); }
  return <Card><h3><Paperclip size={16} aria-hidden="true" /> Файлы полей формы</h3><div className="admin-config-list">{fileFields.flatMap((field) => (attachments[field.key] ?? []).map((attachment) => <div className="admin-config-row" key={attachment.id}><span><strong>{field.label}: {attachment.file_name}</strong><small>{attachment.content_type ?? "Файл"} · {formatSize(attachment.size_bytes)}</small></span><div className="table-actions"><button type="button" className="button button-secondary" onClick={() => void download(attachment)}><Download size={14} />Скачать</button>{canDelete ? <button type="button" className="button button-secondary" onClick={() => void remove(field.key, attachment)}><Trash2 size={14} />Удалить</button> : null}</div></div>))}</div></Card>;
}

function formatSize(size: number) { return size < 1024 ? `${size} Б` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} КБ` : `${(size / 1024 / 1024).toFixed(1)} МБ`; }
