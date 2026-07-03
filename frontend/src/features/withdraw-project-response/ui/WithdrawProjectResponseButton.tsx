import { X } from "lucide-react";
import { useState } from "react";

import type { ProjectResponseStatus } from "../../../entities/project-response/model/types";
import { Button } from "../../../shared/ui/Button";
import { withdrawProjectResponse } from "../api/withdrawProjectResponse";

const withdrawableStatuses: ProjectResponseStatus[] = ["new", "viewed", "contacted"];

export function canWithdrawResponse(status: ProjectResponseStatus) {
  return withdrawableStatuses.includes(status);
}

function getWithdrawButtonLabel(status: ProjectResponseStatus) {
  if (status === "cancelled") {
    return "Отозван";
  }
  if (status === "accepted" || status === "rejected") {
    return "Решение принято";
  }
  return "Отозвать";
}

export function WithdrawProjectResponseButton({
  responseId,
  status,
  onWithdrawn
}: {
  responseId: string;
  status: ProjectResponseStatus;
  onWithdrawn: () => void;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const canWithdraw = canWithdrawResponse(status);

  async function handleWithdraw() {
    const confirmed = window.confirm("Отозвать отклик? После этого можно будет отправить новую заявку на проект.");
    if (!confirmed) {
      return;
    }
    setIsSubmitting(true);
    try {
      await withdrawProjectResponse(responseId);
      onWithdrawn();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Button variant="secondary" onClick={handleWithdraw} disabled={!canWithdraw || isSubmitting}>
      <X size={16} />
      {getWithdrawButtonLabel(status)}
    </Button>
  );
}
