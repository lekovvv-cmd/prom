import type { TextareaHTMLAttributes } from "react";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: string;
};

export function Textarea({
  label,
  id,
  className = "",
  ...props
}: TextareaProps) {
  const inputId = id ?? props.name;
  return (
    <label className={`field ${className}`} htmlFor={inputId}>
      {label && <span>{label}</span>}
      <textarea id={inputId} {...props} />
    </label>
  );
}
