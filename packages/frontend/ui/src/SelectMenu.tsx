import { Check, ChevronDown } from "lucide-react";
import { Select as RadixSelect } from "radix-ui";

export type SelectMenuOption = {
  disabled?: boolean;
  label: string;
  value: string;
};

export function SelectMenu({
  ariaLabel,
  onValueChange,
  options,
  placeholder = "Не выбрано",
  value,
}: {
  ariaLabel: string;
  onValueChange: (value: string) => void;
  options: SelectMenuOption[];
  placeholder?: string;
  value?: string;
}) {
  return (
    <RadixSelect.Root value={value} onValueChange={onValueChange}>
      <RadixSelect.Trigger
        className="select-menu-trigger"
        aria-label={ariaLabel}
      >
        <RadixSelect.Value placeholder={placeholder} />
        <RadixSelect.Icon>
          <ChevronDown aria-hidden="true" size={16} />
        </RadixSelect.Icon>
      </RadixSelect.Trigger>
      <RadixSelect.Portal>
        <RadixSelect.Content className="select-menu-content" position="popper">
          <RadixSelect.Viewport>
            {options.map((option) => (
              <RadixSelect.Item
                className="select-menu-item"
                disabled={option.disabled}
                key={option.value}
                value={option.value}
              >
                <RadixSelect.ItemText>{option.label}</RadixSelect.ItemText>
                <RadixSelect.ItemIndicator>
                  <Check aria-hidden="true" size={14} />
                </RadixSelect.ItemIndicator>
              </RadixSelect.Item>
            ))}
          </RadixSelect.Viewport>
        </RadixSelect.Content>
      </RadixSelect.Portal>
    </RadixSelect.Root>
  );
}
