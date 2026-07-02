import { X } from "lucide-react";

import { Button } from "./Button";

export function Modal({
  title,
  children,
  onClose
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <h2>{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Закрыть">
            <X size={18} />
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
