import { Switch as RadixSwitch } from "radix-ui";

export function Switch({
  checked,
  disabled,
  label,
  onCheckedChange,
}: {
  checked?: boolean;
  disabled?: boolean;
  label: string;
  onCheckedChange?: (checked: boolean) => void;
}) {
  return (
    <label className="switch-field">
      <RadixSwitch.Root
        checked={checked}
        className="switch-control"
        disabled={disabled}
        onCheckedChange={onCheckedChange}
      >
        <RadixSwitch.Thumb className="switch-thumb" />
      </RadixSwitch.Root>
      <span>{label}</span>
    </label>
  );
}
