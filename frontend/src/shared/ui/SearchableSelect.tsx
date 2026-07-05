import { X } from "lucide-react";
import type { KeyboardEvent } from "react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

export type SearchableSelectOption = {
  value: string;
  label: string;
};

function normalizeSearch(value: string) {
  return value.trim().toLocaleLowerCase("ru-RU");
}

export function filterSearchableOptions(options: SearchableSelectOption[], query: string) {
  const terms = normalizeSearch(query).split(/\s+/).filter(Boolean);
  if (terms.length === 0) {
    return options;
  }

  return options.filter((option) => {
    const label = normalizeSearch(option.label);
    return terms.every((term) => label.includes(term));
  });
}

export function SearchableSelect({
  label,
  name,
  value,
  options,
  className = "",
  placeholder = "Не выбрано",
  searchPlaceholder = "Начните вводить",
  emptyText = "Ничего не найдено",
  loadingText = "Загрузка...",
  clearLabel = "Очистить",
  isLoading = false,
  maxVisibleOptions = 50,
  onChange,
  onSearchChange
}: {
  label?: string;
  name?: string;
  value: string;
  options: SearchableSelectOption[];
  className?: string;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyText?: string;
  loadingText?: string;
  clearLabel?: string;
  isLoading?: boolean;
  maxVisibleOptions?: number;
  onChange: (value: string) => void;
  onSearchChange?: (query: string) => void;
}) {
  const generatedId = useId();
  const inputId = name ?? generatedId;
  const listboxId = `${inputId}-listbox`;
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const selectedOption = options.find((option) => option.value === value) ?? null;
  const [query, setQuery] = useState(selectedOption?.label ?? "");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setQuery(selectedOption?.label ?? "");
    }
  }, [isOpen, selectedOption?.label]);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  const matchingOptions = useMemo(() => filterSearchableOptions(options, query), [options, query]);
  const visibleOptions = matchingOptions.slice(0, maxVisibleOptions);
  const hiddenCount = Math.max(0, matchingOptions.length - visibleOptions.length);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [query, options.length]);

  function handleQueryChange(nextQuery: string) {
    setQuery(nextQuery);
    setIsOpen(true);
    onSearchChange?.(nextQuery);
  }

  function selectOption(option: SearchableSelectOption) {
    onChange(option.value);
    setQuery(option.label);
    onSearchChange?.(option.label);
    setIsOpen(false);
  }

  function clearValue() {
    onChange("");
    setQuery("");
    onSearchChange?.("");
    setIsOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((index) => Math.min(index + 1, Math.max(visibleOptions.length - 1, 0)));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setIsOpen(true);
      setHighlightedIndex((index) => Math.max(index - 1, 0));
    }
    if (event.key === "Enter" && isOpen && visibleOptions[highlightedIndex]) {
      event.preventDefault();
      selectOption(visibleOptions[highlightedIndex]);
    }
    if (event.key === "Escape") {
      setIsOpen(false);
      setQuery(selectedOption?.label ?? "");
    }
  }

  const hasValue = value !== "";

  return (
    <div className={`field searchable-select ${className}`} ref={wrapperRef}>
      {label && <label htmlFor={inputId}>{label}</label>}
      <div className="searchable-select-control">
        <input
          id={inputId}
          name={name}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          autoComplete="off"
          placeholder={hasValue ? placeholder : searchPlaceholder}
          role="combobox"
          value={query}
          onChange={(event) => handleQueryChange(event.target.value)}
          onFocus={(event) => {
            setIsOpen(true);
            event.currentTarget.select();
          }}
          onKeyDown={handleKeyDown}
        />
        {hasValue && (
          <button className="select-clear" type="button" aria-label={clearLabel} onClick={clearValue}>
            <X size={14} />
          </button>
        )}
        {isOpen && (
          <div className="searchable-select-menu" id={listboxId} role="listbox">
            {isLoading ? (
              <div className="searchable-select-empty">{loadingText}</div>
            ) : visibleOptions.length === 0 ? (
              <div className="searchable-select-empty">{emptyText}</div>
            ) : (
              <>
                {visibleOptions.map((option, index) => (
                  <button
                    aria-selected={option.value === value}
                    className={index === highlightedIndex ? "searchable-select-option active" : "searchable-select-option"}
                    key={option.value}
                    role="option"
                    type="button"
                    onClick={() => selectOption(option)}
                    onMouseDown={(event) => event.preventDefault()}
                    onMouseEnter={() => setHighlightedIndex(index)}
                  >
                    {option.label}
                  </button>
                ))}
                {hiddenCount > 0 && (
                  <div className="searchable-select-hint">
                    Найдено ещё {hiddenCount}. Уточните запрос.
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
