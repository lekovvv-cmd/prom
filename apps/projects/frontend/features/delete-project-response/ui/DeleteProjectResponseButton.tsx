import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@prom/ui/Button";
import { deleteProjectResponse } from "../api/deleteProjectResponse";

export function DeleteProjectResponseButton({
  responseId,
  onDeleted,
}: {
  responseId: string;
  onDeleted: () => void;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleDelete() {
    const confirmed = window.confirm(
      "Удалить отклик из очереди? Запись останется в базе, но исчезнет из списков и статистики.",
    );
    if (!confirmed) {
      return;
    }
    setIsSubmitting(true);
    try {
      await deleteProjectResponse(responseId);
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
