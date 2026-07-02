export function EmptyState({ title, text }: { title: string; text?: string }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      {text && <p>{text}</p>}
    </div>
  );
}
