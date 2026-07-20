import { Popover as RadixPopover } from "radix-ui";

export function Popover({
  align = "center",
  children,
  trigger,
}: {
  align?: "center" | "end" | "start";
  children: React.ReactNode;
  trigger: React.ReactElement;
}) {
  return (
    <RadixPopover.Root>
      <RadixPopover.Trigger asChild>{trigger}</RadixPopover.Trigger>
      <RadixPopover.Portal>
        <RadixPopover.Content
          align={align}
          className="popover-content"
          sideOffset={8}
        >
          {children}
          <RadixPopover.Arrow className="popover-arrow" />
        </RadixPopover.Content>
      </RadixPopover.Portal>
    </RadixPopover.Root>
  );
}
