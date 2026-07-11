export function formatDuration(seconds: number | null) {
  if (seconds === null) return "Нет данных";
  const minutes = Math.round(seconds / 60);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const rest = minutes % 60;
  return [days ? `${days} д` : "", hours ? `${hours} ч` : "", rest || (!days && !hours) ? `${rest} мин` : ""].filter(Boolean).join(" ");
}
