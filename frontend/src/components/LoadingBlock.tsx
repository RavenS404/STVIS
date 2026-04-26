export function LoadingBlock({ label = "جارٍ التحميل..." }: { label?: string }) {
  return <div className="surface loading-block">{label}</div>;
}
