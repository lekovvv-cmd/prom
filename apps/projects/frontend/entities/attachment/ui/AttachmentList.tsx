import type { Attachment } from "../../project/model/types";
import { apiClient } from "@prom/api-client";
import { useState } from "react";

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
  const [error, setError] = useState<string | null>(null);
  async function download(attachment: Attachment) {
    try {
      setError(null);
      const blob = await apiClient.request<Blob>(
        attachment.download_url.replace(/^\/api/, ""),
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = attachment.file_name;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Не удалось открыть файл",
      );
    }
  }
  if (attachments.length === 0) {
    return <p className="muted">Файлы не прикреплены.</p>;
  }

  return (
    <div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <ul className="attachment-list">
        {attachments.map((attachment) => (
          <li key={attachment.id}>
            <a
              href={attachment.download_url}
              onClick={(event) => {
                event.preventDefault();
                void download(attachment);
              }}
            >
              <span aria-hidden="true">↓</span>
              <span>{attachment.file_name}</span>
            </a>
            <small>{formatSize(attachment.size_bytes)}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
