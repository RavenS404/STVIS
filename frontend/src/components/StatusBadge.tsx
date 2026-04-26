import { translateState } from "../app/presentation";

export function StatusBadge({ state }: { state: string }) {
  return <span className={`badge badge--${state.replace(/_/g, "-")}`}>{translateState(state)}</span>;
}
