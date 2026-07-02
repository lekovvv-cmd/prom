import { useEffect, useState } from "react";

import { getAdminStats } from "../../../entities/project/api/statsApi";
import type { AdminStats } from "../../../entities/project/model/statsTypes";
import { Header } from "../../../widgets/header/ui/Header";
import { Card } from "../../../shared/ui/Card";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";
import { Table } from "../../../shared/ui/Table";

const metricLabels: Array<[keyof AdminStats, string]> = [
  ["projects_total", "Всего проектов"],
  ["projects_active", "Активных"],
  ["projects_archived", "Архивных"],
  ["responses_total", "Всего откликов"],
  ["responses_new", "Новых откликов"],
  ["responses_accepted", "Принятых"],
  ["responses_rejected", "Отклонённых"]
];

export function AdminStatsPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        setIsLoading(true);
        setError(null);
        setStats(await getAdminStats());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось загрузить статистику");
      } finally {
        setIsLoading(false);
      }
    }
    void loadStats();
  }, []);

  return (
    <>
      <Header />
      <PageLayout title="Статистика витрины" subtitle="Базовые показатели проектов и откликов">
        {error && <p className="form-error">{error}</p>}
        {isLoading && <Spinner />}
        {stats && (
          <>
            <div className="stats-grid">
              {metricLabels.map(([key, label]) => (
                <Card key={key} className="metric-card">
                  <span>{label}</span>
                  <strong>{stats[key] as number}</strong>
                </Card>
              ))}
            </div>
            <Card>
              <h2>Отклики по проектам</h2>
              <Table>
                <table>
                  <thead>
                    <tr>
                      <th>Проект</th>
                      <th>Отклики</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.responses_by_project.map((item) => (
                      <tr key={item.project_id}>
                        <td>{item.project_title}</td>
                        <td>{item.responses_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Table>
            </Card>
          </>
        )}
      </PageLayout>
    </>
  );
}
