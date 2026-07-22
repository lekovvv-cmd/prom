import { AlertDialog as Primitive } from "radix-ui";

import { Button } from "./Button";

export function AlertDialog({
  cancelLabel = "Отмена",
  confirmLabel,
  description,
  onConfirm,
  title,
  trigger,
}: {
  cancelLabel?: string;
  confirmLabel: string;
  description: string;
  onConfirm: () => void;
  title: string;
  trigger: React.ReactNode;
}) {
  return (
    <Primitive.Root>
      <Primitive.Trigger asChild>{trigger}</Primitive.Trigger>
      <Primitive.Portal>
        <Primitive.Overlay className="modal-backdrop" />
        <Primitive.Content className="modal" aria-describedby={undefined}>
          <Primitive.Title>{title}</Primitive.Title>
          <Primitive.Description>{description}</Primitive.Description>
          <div className="form-actions">
            <Primitive.Cancel asChild>
              <Button variant="ghost">{cancelLabel}</Button>
            </Primitive.Cancel>
            <Primitive.Action asChild>
              <Button variant="danger" onClick={onConfirm}>
                {confirmLabel}
              </Button>
            </Primitive.Action>
          </div>
        </Primitive.Content>
      </Primitive.Portal>
    </Primitive.Root>
  );
}
