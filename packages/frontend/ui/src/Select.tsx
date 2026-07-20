import type { SelectHTMLAttributes } from "react";
import { X } from "lucide-react";

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  clearLabel?: string;
  isClearable?: boolean;
  onClear?: () => void;
};

export function Select({
  label,
  id,
  className = "",
  children,
  clearLabel = "Очистить",
  isClearable = false,
  onClear,
  ...props
}: SelectProps) {
  const inputId = id ?? props.name;
  const hasValue =
    props.value !== undefined && props.value !== null && props.value !== "";

  return (
    <label className={`field ${className}`} htmlFor={inputId}>
      {label && <span>{label}</span>}
      <span className="select-control">
        <select id={inputId} {...props}>
          {children}
        </select>
        {isClearable && hasValue && onClear && (
          <button
            className="select-clear"
            type="button"
            aria-label={clearLabel}
            onClick={onClear}
          >
            <X size={14} />
          </button>
        )}
      </span>
    </label>
  );
}
