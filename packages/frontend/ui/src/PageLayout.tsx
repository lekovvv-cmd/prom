import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { keepShortRussianWords } from "./typography";

export function PageLayout({
  title,
  subtitle,
  actions,
  backLink,
  children,
}: {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  backLink?: { to: string; label: string };
  children: React.ReactNode;
}) {
  return (
    <main className="page">
      {backLink && (
        <Link className="page-back-link" to={backLink.to}>
          <ArrowLeft size={16} aria-hidden="true" />
          {backLink.label}
        </Link>
      )}
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
