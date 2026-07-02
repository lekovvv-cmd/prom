export function Spinner({ label = "Загрузка" }: { label?: string }) {
  return (
    <div className="spinner-wrap" role="status">
      <span className="spinner" />
      <span>{label}</span>
    </div>
  );
}
