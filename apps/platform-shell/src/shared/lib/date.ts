export function formatDate(value?: string | null) {
  if (!value) {
    return "Не указана";
  }
  return new Intl.DateTimeFormat("ru-RU").format(new Date(value));
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "Не указано";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}
