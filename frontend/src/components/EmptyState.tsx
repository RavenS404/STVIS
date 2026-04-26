export function EmptyState({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="surface empty-state">
      <h3>{title}</h3>
      {subtitle ? <p>{subtitle}</p> : null}
    </div>
  );
}
