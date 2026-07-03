import type { ChangeEvent } from "react";
import { Paperclip, X } from "lucide-react";

function getFileKey(file: File) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} Б`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} КБ`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} МБ`;
}

export function FileInput({
  files,
  label,
  onChange
}: {
  files: File[];
  label: string;
  onChange: (files: File[]) => void;
}) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files ?? []);
    const fileKeys = new Set(files.map(getFileKey));
    const nextFiles = [...files];

    selectedFiles.forEach((file) => {
      const key = getFileKey(file);
      if (!fileKeys.has(key)) {
        fileKeys.add(key);
        nextFiles.push(file);
      }
    });

    onChange(nextFiles);
    event.target.value = "";
  }

  function removeFile(fileToRemove: File) {
    const removedFileKey = getFileKey(fileToRemove);
    onChange(files.filter((file) => getFileKey(file) !== removedFileKey));
  }

  return (
    <div className="file-input">
      <label className="file-input-trigger">
        <Paperclip size={18} />
        <span>{label}</span>
        <small>Можно выбрать несколько файлов, до 10 МБ каждый</small>
        <input className="file-input-control" type="file" multiple onChange={handleChange} />
      </label>
      {files.length > 0 ? (
        <ul className="file-selection-list" aria-label="Выбранные файлы">
          {files.map((file) => (
            <li key={getFileKey(file)}>
              <span>
                <strong>{file.name}</strong>
                <small>{formatFileSize(file.size)}</small>
              </span>
              <button type="button" aria-label={`Убрать файл ${file.name}`} onClick={() => removeFile(file)}>
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <span className="file-input-empty">Файлы не выбраны</span>
      )}
    </div>
  );
}
