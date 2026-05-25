import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { fetchSystemHealth } from "../services/health";

const SERVICE_LABELS: Record<string, string> = {
  backend: "الخادم",
  database: "قاعدة البيانات",
  object_storage: "التخزين",
  rabbitmq: "طابور المهام",
  worker: "المعالج",
  "celery-worker": "عامل Celery",
  "model:violation_detection": "نموذج المخالفات",
  "model:plate_detection": "نموذج اللوحات",
};

function renderDetails(details: Record<string, unknown>) {
  const entries = Object.entries(details).filter(
    ([, value]) => value !== null && value !== undefined && value !== "",
  );
  if (!entries.length) return null;
  return (
    <details className="health-details">
      <summary className="ghost-button health-details__summary">عرض التفاصيل</summary>
      <div className="health-details__content">
        {entries.map(([key, value]) => (
          <div key={key} className="health-detail-row">
            <span className="eyebrow">{key}</span>
            <span className="health-detail-row__value">{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
          </div>
        ))}
      </div>
    </details>
  );
}

export function HealthPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["health"], queryFn: fetchSystemHealth, refetchInterval: 30_000 });

  if (isLoading) return <LoadingBlock />;
  if (isError) return <EmptyState title="تعذر تحميل حالة النظام" subtitle="حاولي تحديث الصفحة مرة أخرى." />;
  if (!data) return <EmptyState title="لا توجد بيانات صحة" />;

  const components = data.components ?? {};

  return (
    <div className="page-grid">
      <section className="surface">
        <div className="panel-header">
          <h2>حالة النظام</h2>
          <span className="eyebrow">{data.generated_at ? new Date(data.generated_at).toLocaleString("ar-EG") : ""}</span>
        </div>
      </section>
      <div className="health-grid">
        {Object.entries(components).map(([key, value]) => (
          <div key={key} className="surface health-card">
            <div className="health-card__header">
              <strong>{SERVICE_LABELS[key] ?? key}</strong>
              <StatusBadge state={value.status} />
            </div>
            {renderDetails(value.details ?? {})}
          </div>
        ))}
        {!Object.keys(components).length && <EmptyState title="لا توجد مكونات مسجلة بعد" />}
      </div>
    </div>
  );
}
