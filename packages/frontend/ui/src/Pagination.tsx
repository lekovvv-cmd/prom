import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "./Button";

export function Pagination({
  page,
  pageCount,
  onPageChange,
}: {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
}) {
  return (
    <nav className="pagination" aria-label="Пагинация">
      <Button
        aria-label="Предыдущая страница"
        disabled={page <= 1}
        size="sm"
        variant="secondary"
        onClick={() => onPageChange(page - 1)}
      >
        <ChevronLeft aria-hidden="true" size={16} />
      </Button>
      <span aria-live="polite">
        Страница {page} из {Math.max(pageCount, 1)}
      </span>
      <Button
        aria-label="Следующая страница"
        disabled={page >= pageCount}
        size="sm"
        variant="secondary"
        onClick={() => onPageChange(page + 1)}
      >
        <ChevronRight aria-hidden="true" size={16} />
      </Button>
    </nav>
  );
}
