import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { fetchAuditLogs } from "../services/audit";

export function AuditPage() {
  const { data, isLoading } = useQuery({ queryKey: ["audit"], queryFn: () => fetchAuditLogs(1) });

  if (isLoading) return <LoadingBlock />;
  if (!data?.items.length) return <EmptyState title="لا توجد سجلات تدقيق" />;

  return (
    <section className="surface">
      <div className="panel-header">
        <h2>سجل التدقيق</h2>
      </div>
      <div className="table-like">
        {data.items.map((item) => (
          <div key={item.id} className="table-row">
            <div>
              <strong>{item.summary_ar}</strong>
              <small>{item.entity_type} / {item.entity_id}</small>
            </div>
            <span>{item.actor_role ?? "system"}</span>
            <span>{new Date(item.occurred_at).toLocaleString("ar-EG")}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
