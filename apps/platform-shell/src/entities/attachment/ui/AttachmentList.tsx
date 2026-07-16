import type { Attachment } from "../../project/model/types";
import { env } from "../../../shared/config/env";

function formatSize(size: number) {
  if (size < 1024) {
    return `${size} Б`;
  }
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} КБ`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} МБ`;
}

export function AttachmentList({ attachments }: { attachments: Attachment[] }) {
  if (attachments.length === 0) {
    return <p className="muted">Файлы не прикреплены.</p>;
  }

  return (
    <ul className="attachment-list">
      {attachments.map((attachment) => (
        <li key={attachment.id}>
          <a href={`${env.fileBaseUrl}${attachment.download_url}`} target="_blank" rel="noreferrer">
            <span aria-hidden="true">↓</span>
            <span>{attachment.file_name}</span>
          </a>
          <small>{formatSize(attachment.size_bytes)}</small>
        </li>
      ))}
    </ul>
  );
}
