import { AlertTriangle } from "lucide-react";

import { Button } from "./Button";

export function ErrorState({
  message,
  onRetry,
  title = "Не удалось загрузить данные",
}: {
  message?: string;
  onRetry?: () => void;
  title?: string;
}) {
  return (
    <section
      className="grid gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-900"
      role="alert"
    >
      <AlertTriangle aria-hidden size={22} />
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
      {onRetry ? <Button onClick={onRetry}>Повторить</Button> : null}
    </section>
  );
}
