import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "../../../shared/ui/Button";
import { deleteArchivedProject } from "../api/deleteArchivedProject";

export function DeleteArchivedProjectButton({ projectId, onDeleted }: { projectId: string; onDeleted: () => void }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleDelete() {
    const confirmed = window.confirm(
      "Удалить проект из архива? Запись останется в базе данных, но исчезнет из списка архива."
    );
    if (!confirmed) {
      return;
    }
    setIsSubmitting(true);
    try {
      await deleteArchivedProject(projectId);
      onDeleted();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Button variant="danger" onClick={handleDelete} disabled={isSubmitting}>
      <Trash2 size={16} />
      Удалить
    </Button>
  );
}
