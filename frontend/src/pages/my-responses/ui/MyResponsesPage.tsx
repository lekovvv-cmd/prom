import { useEffect, useState } from "react";

import { getMyResponses } from "../../../entities/project-response/api/projectResponseApi";
import type { ProjectResponse } from "../../../entities/project-response/model/types";
import { Header } from "../../../widgets/header/ui/Header";
import { MyResponsesTable } from "../../../widgets/my-responses-table/ui/MyResponsesTable";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function MyResponsesPage() {
  const [responses, setResponses] = useState<ProjectResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadResponses() {
    try {
      setIsLoading(true);
      setError(null);
      const payload = await getMyResponses({ limit: 100 });
      setResponses(payload.items);
      setTotal(payload.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить ваши отклики");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadResponses();
  }, []);

  return (
    <>
      <Header />
      <PageLayout
        title="Мои отклики"
        subtitle={`${total} ${total === 1 ? "заявка" : "заявок"} на участие в проектах`}
      >
        {error && <p className="form-error">{error}</p>}
        {isLoading ? <Spinner /> : <MyResponsesTable responses={responses} onUpdated={loadResponses} />}
      </PageLayout>
    </>
  );
}
