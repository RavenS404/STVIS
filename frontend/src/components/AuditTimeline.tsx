import type { AuditLog } from "../app/types";

export function AuditTimeline({ items }: { items: AuditLog[] }) {
  return (
    <div className="surface timeline">
      <div className="panel-header">
        <h3>الخط الزمني للتدقيق</h3>
      </div>
      <div className="timeline-list">
        {items.map((item) => (
          <div key={item.id} className="timeline-item">
            <div>
              <strong>{item.summary_ar}</strong>
              <small>{item.action_type}</small>
            </div>
            <span>{new Date(item.occurred_at).toLocaleString("ar-EG")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
