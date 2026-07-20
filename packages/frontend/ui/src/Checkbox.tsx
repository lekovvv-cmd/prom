import { Check } from "lucide-react";
import { Checkbox as RadixCheckbox } from "radix-ui";

export function Checkbox({
  checked,
  disabled,
  label,
  onCheckedChange,
}: {
  checked?: boolean | "indeterminate";
  disabled?: boolean;
  label: string;
  onCheckedChange?: (checked: boolean | "indeterminate") => void;
}) {
  return (
    <label className="checkbox-field">
      <RadixCheckbox.Root
        checked={checked}
        className="checkbox-control"
        disabled={disabled}
        onCheckedChange={onCheckedChange}
      >
        <RadixCheckbox.Indicator>
          <Check aria-hidden="true" size={14} />
        </RadixCheckbox.Indicator>
      </RadixCheckbox.Root>
      <span>{label}</span>
    </label>
  );
}
