export function ConfidenceBadge({ value }: { value?: number | null }) {
  if (value == null) return <span className="badge badge--muted">غير متاح</span>;
  const css = value >= 0.82 ? "good" : value >= 0.65 ? "warning" : "bad";
  return <span className={`badge badge--${css}`}>{(value * 100).toFixed(1)}%</span>;
}
