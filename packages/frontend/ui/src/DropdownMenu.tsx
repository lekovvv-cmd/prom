import { DropdownMenu as RadixDropdownMenu } from "radix-ui";

export type DropdownMenuItem = {
  disabled?: boolean;
  label: string;
  onSelect: () => void;
};

export function DropdownMenu({
  items,
  trigger,
}: {
  items: DropdownMenuItem[];
  trigger: React.ReactElement;
}) {
  return (
    <RadixDropdownMenu.Root>
      <RadixDropdownMenu.Trigger asChild>{trigger}</RadixDropdownMenu.Trigger>
      <RadixDropdownMenu.Portal>
        <RadixDropdownMenu.Content
          align="end"
          className="dropdown-menu-content"
          sideOffset={6}
        >
          {items.map((item) => (
            <RadixDropdownMenu.Item
              className="dropdown-menu-item"
              disabled={item.disabled}
              key={item.label}
              onSelect={item.onSelect}
            >
              {item.label}
            </RadixDropdownMenu.Item>
          ))}
        </RadixDropdownMenu.Content>
      </RadixDropdownMenu.Portal>
    </RadixDropdownMenu.Root>
  );
}
