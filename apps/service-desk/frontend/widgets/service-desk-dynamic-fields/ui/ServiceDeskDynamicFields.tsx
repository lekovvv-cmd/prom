import type { ReactNode } from "react";

import type { ServiceDeskTemplateField } from "../../../entities/service-desk-catalog/model/types";
import {
  getFieldOptions,
  isFieldRequired,
  isFieldVisible,
  normalizeFieldValue,
  type FormValues,
} from "../../../entities/service-desk-catalog/model/rules";

type UserOption = { id: string; display_name: string };

export function ServiceDeskDynamicFields({
  fields,
  values,
  onChange,
  mode = "edit",
  users = [],
  errors = {},
  renderFileField,
}: {
  fields: ServiceDeskTemplateField[];
  values: FormValues;
  onChange: (key: string, value: unknown) => void;
  mode?: "edit" | "preview" | "readonly";
  users?: UserOption[];
  errors?: Record<string, string>;
  renderFileField?: (
    field: ServiceDeskTemplateField,
    required: boolean,
    error?: string,
  ) => ReactNode;
}) {
  const disabled = mode === "readonly";
  return (
    <>
      {fields
        .filter((field) => isFieldVisible(field, values))
        .sort((a, b) => a.position - b.position)
        .map((field) => {
          const required = isFieldRequired(field, values);
          const label = `${field.label}${required ? " *" : ""}`;
          const options = getFieldOptions(field);
          const error = errors[field.key];
          const errorId = `${field.key}-error`;
          const common = {
            id: field.key,
            name: field.key,
            disabled,
            "aria-invalid": Boolean(error),
            "aria-describedby": error ? errorId : undefined,
          };
          if (field.field_type === "file" && renderFileField)
            return (
              <div key={field.id}>
                {renderFileField(field, required, error)}
              </div>
            );
          return (
            <label
              className={`field ${["textarea", "rich_text"].includes(field.field_type) ? "field-wide" : ""} ${field.field_type === "checkbox" ? "service-desk-checkbox-field" : ""}`}
              key={field.id}
            >
              {field.field_type === "checkbox" ? null : <span>{label}</span>}
              {field.field_type === "select" || field.field_type === "user" ? (
                <select
                  {...common}
                  value={String(values[field.key] ?? "")}
                  onChange={(event) => onChange(field.key, event.target.value)}
                >
                  <option value="">Выберите значение</option>
                  {(field.field_type === "user"
                    ? users.map((user) => ({
                        label: user.display_name,
                        value: user.id,
                      }))
                    : options
                  ).map((option) => (
                    <option
                      key={String(option.value)}
                      value={String(option.value)}
                    >
                      {option.label ?? option.value}
                    </option>
                  ))}
                </select>
              ) : field.field_type === "multiselect" ? (
                <select
                  {...common}
                  multiple
                  value={
                    Array.isArray(values[field.key])
                      ? (values[field.key] as unknown[]).map(String)
                      : []
                  }
                  onChange={(event) =>
                    onChange(
                      field.key,
                      Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    )
                  }
                >
                  {options.map((option) => (
                    <option
                      key={String(option.value)}
                      value={String(option.value)}
                    >
                      {option.label ?? option.value}
                    </option>
                  ))}
                </select>
              ) : field.field_type === "checkbox" ? (
                <span className="checkbox-field service-desk-checkbox-control">
                  <input
                    {...common}
                    className="checkbox-control"
                    type="checkbox"
                    checked={Boolean(values[field.key])}
                    onChange={(event) =>
                      onChange(field.key, event.target.checked)
                    }
                  />
                  <span>{label}</span>
                </span>
              ) : field.field_type === "file" ? (
                <input
                  {...common}
                  type="file"
                  multiple
                  onChange={(event) =>
                    onChange(
                      field.key,
                      Array.from(event.target.files ?? [], (file) => file.name),
                    )
                  }
                />
              ) : ["textarea", "rich_text"].includes(field.field_type) ? (
                <textarea
                  {...common}
                  rows={4}
                  placeholder={field.placeholder ?? undefined}
                  value={String(values[field.key] ?? "")}
                  onChange={(event) => onChange(field.key, event.target.value)}
                />
              ) : field.field_type === "text" && options.length ? (
                <>
                  <input
                    {...common}
                    type="text"
                    list={`${field.id}-options`}
                    autoComplete="off"
                    placeholder={field.placeholder ?? undefined}
                    value={String(values[field.key] ?? "")}
                    onChange={(event) =>
                      onChange(field.key, event.target.value)
                    }
                  />
                  <datalist id={`${field.id}-options`}>
                    {options.map((option) => {
                      const label = String(option.label ?? option.value ?? "");
                      return label ? (
                        <option
                          key={String(option.value ?? label)}
                          value={label}
                        />
                      ) : null;
                    })}
                  </datalist>
                </>
              ) : (
                <input
                  {...common}
                  type={inputType(field.field_type)}
                  placeholder={field.placeholder ?? undefined}
                  value={String(values[field.key] ?? "")}
                  onChange={(event) =>
                    onChange(
                      field.key,
                      normalizeFieldValue(field.field_type, event.target.value),
                    )
                  }
                />
              )}
              {field.help_text ? (
                <small className="field-help">{field.help_text}</small>
              ) : null}
              {validationHint(field) ? (
                <small className="field-help">{validationHint(field)}</small>
              ) : null}
              {error ? (
                <small id={errorId} className="field-error">
                  {error}
                </small>
              ) : null}
            </label>
          );
        })}
    </>
  );
}

function inputType(fieldType: string) {
  if (fieldType === "number") return "number";
  if (fieldType === "date") return "date";
  if (fieldType === "time") return "time";
  if (fieldType === "datetime") return "datetime-local";
  if (fieldType === "email") return "email";
  return "text";
}

function validationHint(field: ServiceDeskTemplateField) {
  const validation = field.validation ?? {};
  const hints = [];
  if (validation.min_length != null)
    hints.push(`минимум ${validation.min_length} символов`);
  if (validation.max_length != null)
    hints.push(`максимум ${validation.max_length} символов`);
  if (validation.min != null) hints.push(`от ${validation.min}`);
  if (validation.max != null) hints.push(`до ${validation.max}`);
  return hints.join("; ");
}
