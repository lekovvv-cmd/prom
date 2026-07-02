import { Archive } from "lucide-react";
import { useState } from "react";

import { Button } from "../../../shared/ui/Button";
import { archiveProject } from "../api/archiveProject";

export function ArchiveProjectButton({ projectId, onArchived }: { projectId: string; onArchived: () => void }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleArchive() {
    const confirmed = window.confirm("Архивировать проект? Он исчезнет из публичной витрины.");
    if (!confirmed) {
      return;
    }
    setIsSubmitting(true);
    try {
      await archiveProject(projectId);
      onArchived();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Button variant="danger" onClick={handleArchive} disabled={isSubmitting}>
      <Archive size={16} />
      Архив
    </Button>
  );
}
