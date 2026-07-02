import type { ChangeEvent } from "react";

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
    onChange(Array.from(event.target.files ?? []));
  }

  return (
    <label className="file-input">
      <span>
        <span aria-hidden="true">+</span>
        {label}
      </span>
      <input type="file" multiple onChange={handleChange} />
      {files.length > 0 && <small>{files.map((file) => file.name).join(", ")}</small>}
    </label>
  );
}
