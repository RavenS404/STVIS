export function StatCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <div className="surface stat-card">
      <p>{title}</p>
      <strong>{value}</strong>
      {subtitle ? <span>{subtitle}</span> : null}
    </div>
  );
}
