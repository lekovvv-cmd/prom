import { keepShortRussianWords } from "./typography";

export function PageLayout({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <main className="page">
      <div className="page-title-row">
        <div>
          <h1>{title}</h1>
          {subtitle && (
            <p>
              {typeof subtitle === "string"
                ? keepShortRussianWords(subtitle)
                : subtitle}
            </p>
          )}
        </div>
        {actions && <div className="page-actions">{actions}</div>}
      </div>
      {children}
    </main>
  );
}
