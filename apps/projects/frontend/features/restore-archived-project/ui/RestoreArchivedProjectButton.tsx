import { ArchiveRestore } from "lucide-react";
import { useState } from "react";

import { Button } from "@prom/ui/Button";
import { restoreArchivedProject } from "../api/restoreArchivedProject";

export function RestoreArchivedProjectButton({
  projectId,
  onRestored,
}: {
  projectId: string;
  onRestored: () => void;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleRestore() {
    const confirmed = window.confirm(
      "Вернуть проект из архива в текущие проекты?",
    );
    if (!confirmed) {
      return;
    }
    setIsSubmitting(true);
    try {
      await restoreArchivedProject(projectId);
      onRestored();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Button variant="secondary" onClick={handleRestore} disabled={isSubmitting}>
      <ArchiveRestore size={16} />
      Вернуть
    </Button>
  );
}
