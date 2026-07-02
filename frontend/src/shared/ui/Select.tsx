import type { SelectHTMLAttributes } from "react";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
};

export function Select({ label, id, className = "", children, ...props }: SelectProps) {
  const inputId = id ?? props.name;
  return (
    <label className={`field ${className}`} htmlFor={inputId}>
      {label && <span>{label}</span>}
      <select id={inputId} {...props}>
        {children}
      </select>
    </label>
  );
}
