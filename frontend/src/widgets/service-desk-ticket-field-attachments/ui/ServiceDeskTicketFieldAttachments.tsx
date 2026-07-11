import { useEffect, useState } from "react";
import { Download, Paperclip } from "lucide-react";

import { downloadServiceDeskAttachment, listServiceDeskFieldAttachments } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskAttachment } from "../../../entities/service-desk-ticket/model/types";
import { Card } from "../../../shared/ui/Card";

export function ServiceDeskTicketFieldAttachments({ ticketId, fields }: { ticketId: string; fields: Array<{ key: string; label: string; type: string }> }) {
  const fileFields = fields.filter((field) => field.type === "file");
  const fieldKeys = fileFields.map((field) => field.key).join("|");
  const [attachments, setAttachments] = useState<Record<string, ServiceDeskAttachment[]>>({});
  useEffect(() => { let active = true; Promise.all(fileFields.map(async (field) => [field.key, await listServiceDeskFieldAttachments(ticketId, field.key)] as const)).then((items) => { if (active) setAttachments(Object.fromEntries(items)); }).catch(() => undefined); return () => { active = false; }; }, [ticketId, fieldKeys]);
  if (!fileFields.some((field) => (attachments[field.key] ?? []).length)) return null;
  async function download(attachment: ServiceDeskAttachment) { const blob = await downloadServiceDeskAttachment(ticketId, attachment.id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = attachment.file_name; link.click(); URL.revokeObjectURL(url); }
  return <Card><h3><Paperclip size={16} aria-hidden="true" /> Файлы полей формы</h3><div className="admin-config-list">{fileFields.flatMap((field) => (attachments[field.key] ?? []).map((attachment) => <div className="admin-config-row" key={attachment.id}><span><strong>{field.label}: {attachment.file_name}</strong><small>{attachment.content_type ?? "Файл"} · {formatSize(attachment.size_bytes)}</small></span><button type="button" className="button button-secondary" onClick={() => void download(attachment)}><Download size={14} />Скачать</button></div>))}</div></Card>;
}

function formatSize(size: number) { return size < 1024 ? `${size} Б` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} КБ` : `${(size / 1024 / 1024).toFixed(1)} МБ`; }
