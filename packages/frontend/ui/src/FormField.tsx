import { useId } from "react";

export function FormField({
  children,
  description,
  error,
  label,
  required,
}: {
  children: (props: {
    "aria-describedby"?: string;
    "aria-invalid": boolean;
    id: string;
  }) => React.ReactNode;
  description?: string;
  error?: string;
  label: string;
  required?: boolean;
}) {
  const id = useId();
  const descriptionId = description ? `${id}-description` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy =
    [descriptionId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="form-field">
      <label htmlFor={id}>
        {label}
        {required ? <span aria-hidden="true"> *</span> : null}
      </label>
      {children({
        "aria-describedby": describedBy,
        "aria-invalid": Boolean(error),
        id,
      })}
      {description ? (
        <small id={descriptionId} className="form-field-description">
          {description}
        </small>
      ) : null}
      {error ? (
        <small id={errorId} className="form-field-error" role="alert">
          {error}
        </small>
      ) : null}
    </div>
  );
}
