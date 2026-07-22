export function Panel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-md border border-slate-200 bg-white p-4 ${className}`}
    >
      {children}
    </section>
  );
}
