import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export function Input({ label, id, className = "", ...props }: InputProps) {
  const inputId = id ?? props.name;
  return (
    <label className={`field ${className}`} htmlFor={inputId}>
      {label && <span>{label}</span>}
      <input id={inputId} {...props} />
    </label>
  );
}
